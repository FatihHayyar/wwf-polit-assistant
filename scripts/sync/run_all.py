from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from app.db.database import engine
from app.core.file_io import atomic_write_json
from app.services.notification_email_service import (
    send_pending_notifications,
)


SYNC_MODULES = [
    ("Affairs", "scripts.sync.incremental_sync"),
    ("Agendas", "scripts.sync.agendas_sync"),
    ("Meetings", "scripts.sync.meetings_sync"),
    ("Votings", "scripts.sync.votings_sync"),
    ("Events", "scripts.sync.events_sync"),
    ("Documents", "scripts.sync.docs_sync"),
    ("Texts", "scripts.sync.texts_sync"),
    ("Groups", "scripts.sync.groups_sync"),
    ("Interest Declarations", "scripts.sync.interests_sync"),
]

SYNC_LOCK_ID = 2026100801

RUN_ID = os.environ.get("SYNC_RUN_ID") or uuid.uuid4().hex
RESULT_FILE = os.environ.get("SYNC_RESULT_FILE") or str(
    Path(__file__).resolve().parents[2] / "logs" / f"sync_{RUN_ID}.json"
)
CANCEL_FILE = Path(RESULT_FILE).with_suffix(".cancel")
RESUME_FILE = os.environ.get("SYNC_RESUME_FILE")
DATASET_KEYS = {"Affairs": "affairs", "Agendas": "agendas", "Meetings": "meetings",
                "Votings": "votings", "Events": "events", "Documents": "docs",
                "Texts": "texts", "Groups": "groups", "Interest Declarations": "interests"}


class SyncCancelled(Exception):
    pass


def check_cancelled() -> None:
    if CANCEL_FILE.exists():
        raise SyncCancelled("Cancellation requested by administrator.")


def run_dataset(module: str) -> int:
    check_cancelled()
    process = subprocess.Popen([sys.executable, "-u", "-m", module])
    try:
        while process.poll() is None:
            check_cancelled()
            time.sleep(1)
        check_cancelled()
        return process.returncode
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_result(result: dict) -> None:
    if not RESULT_FILE:
        return

    atomic_write_json(Path(RESULT_FILE), result, indent=2)


def notify_parent(message: str) -> None:
    ready_file = os.environ.get("SYNC_READY_FILE")

    if not ready_file:
        return

    path = Path(ready_file)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(message + "\n", encoding="utf-8")
    except OSError as exc:
        print(
            f"Could not write sync startup status: {exc}",
            file=sys.stderr,
            flush=True,
        )


def initial_result() -> dict:
    result = {
        "run_id": RUN_ID,
        "status": "running",
        "started_at": now_iso(),
        "finished_at": None,
        "duration_seconds": None,
        "datasets": {
            "total": len(SYNC_MODULES),
            "successful": 0,
            "failed": 0,
        },
        "records": {
            "new": 0,
            "changed": 0,
            "unchanged": 0,
            "errors": 0,
        },
        "notifications": {
            "emails_sent": 0,
            "emails_failed": 0,
        },
        "error_message": None,
        "current_dataset": None,
        "process_id": os.getpid(),
        "cancellable": True,
        "job_id": os.environ.get("SYNC_JOB_ID", RUN_ID),
        "resume_of": None,
        "dataset_results": {},
    }
    if RESUME_FILE:
        parent = json.loads(Path(RESUME_FILE).read_text(encoding="utf-8"))
        result["resume_of"] = parent["run_id"]
        result["dataset_results"] = {name: detail for name, detail in parent.get("dataset_results", {}).items()
                                     if detail["status"] == "completed"}
        if not parent.get("dataset_results"):
            # Compatibility for runs before stage manifests existed. Only an
            # explicit runner OK marker proves that a legacy stage completed.
            import re
            log = Path(RESUME_FILE).with_suffix(".log").read_text(encoding="utf-8", errors="replace")
            snapshot = checkpoint_snapshot()
            for name in re.findall(r"^\[\d+/\d+\] OK: (.*?) \(", log, re.MULTILINE):
                if name in DATASET_KEYS:
                    result["dataset_results"][name] = {"status": "completed", "records": snapshot.get(DATASET_KEYS[name], {}), "legacy": True}
    # Recover a stage whose worker committed completion just before its runner
    # exited without recording the OK marker.
    from scripts.sync.source_batches import job_directory
    directory = job_directory()
    if directory:
        for name, key in DATASET_KEYS.items():
            path = directory / f"{'documents' if key == 'docs' else key}.json"
            if path.exists():
                state = json.loads(path.read_text(encoding="utf-8"))
                if state.get("complete"):
                    result["dataset_results"][name] = {"status": "completed", "records": {
                        "new": state["counts"]["NEW"], "changed": state["counts"]["CHANGED"],
                        "unchanged": state["counts"]["UNCHANGED"], "errors": state["counts"]["ERROR"]}}
    recompute_totals(result)
    return result


def recompute_totals(result):
    details = result["dataset_results"].values()
    result["datasets"]["successful"] = sum(d["status"] == "completed" for d in details)
    result["datasets"]["failed"] = sum(d["status"] == "failed" for d in details)
    result["records"] = {key: sum(d.get("records", {}).get(key, 0) for d in result["dataset_results"].values())
                         for key in ("new", "changed", "unchanged", "errors")}


def checkpoint_snapshot() -> dict:
    query = text(
        """
        SELECT
            dataset,
            records_new,
            records_changed,
            records_unchanged,
            records_error
        FROM sync_checkpoints
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    return {
        row["dataset"]: {
            "new": row["records_new"] or 0,
            "changed": row["records_changed"] or 0,
            "unchanged": row["records_unchanged"] or 0,
            "errors": row["records_error"] or 0,
        }
        for row in rows
    }


def run_all_syncs(result: dict) -> None:
    started_at = datetime.now()
    total = len(SYNC_MODULES)

    print("=" * 70, flush=True)
    print("WWF POLIT-ASSISTANT - ALL DATASET SYNC", flush=True)
    print("=" * 70, flush=True)
    print(f"Start: {started_at}", flush=True)
    print(f"Datasets: {total}", flush=True)

    for index, (name, module) in enumerate(SYNC_MODULES, start=1):
        check_cancelled()
        if result["dataset_results"].get(name, {}).get("status") == "completed":
            print(f"[{index}/{total}] SKIP: {name} (already committed in this job)", flush=True)
            continue
        result["current_dataset"] = name
        result["dataset_results"][name] = {"status": "running"}
        save_result(result)
        print("\n" + "=" * 70, flush=True)
        print(f"[{index}/{total}] START: {name}", flush=True)
        print(f"Module: {module}", flush=True)
        print("=" * 70, flush=True)

        start_time = time.monotonic()

        try:
            returncode = run_dataset(module)
        except KeyboardInterrupt:
            raise SystemExit(130)

        duration = time.monotonic() - start_time
        result["dataset_results"][name] = {
            "status": "failed" if returncode else "completed", "duration_seconds": round(duration, 2),
            "records": checkpoint_snapshot().get(DATASET_KEYS[name], {})}
        recompute_totals(result)

        if returncode != 0:
            with engine.connect() as db:
                reason = db.scalar(text("SELECT error_message FROM sync_checkpoints WHERE dataset=:dataset"), {"dataset": DATASET_KEYS[name]})
            result["error_message"] = (
                f"{name} sync failed "
                f"(exit code {returncode})." + (f" {reason}" if reason else "")
            )
            result["dataset_results"][name]["error_message"] = result["error_message"]
            save_result(result)

            print(
                f"SYNC FAILED: {name} "
                f"(exit code {returncode})",
                flush=True,
            )

            continue

        save_result(result)

        print(
            f"\n[{index}/{total}] OK: {name} "
            f"({duration:.1f} seconds)",
            flush=True,
        )

    print("\n" + "=" * 70, flush=True)
    print("DATASET SYNCS FINISHED WITH FAILURES" if result["datasets"]["failed"] else "ALL DATASET SYNCS COMPLETED", flush=True)
    print(
        f"Successful: "
        f"{result['datasets']['successful']}/{total}",
        flush=True,
    )


def send_notification_emails(result: dict) -> None:
    print("\n" + "=" * 70, flush=True)
    print("SENDING PENDING NOTIFICATION EMAILS", flush=True)
    print("=" * 70, flush=True)

    def progress(sent, failed):
        result["notifications"]["emails_sent"] = sent
        result["notifications"]["emails_failed"] = failed
        if (sent + failed) % 100 == 0:
            save_result(result)

    try:
        sent, failed = send_pending_notifications(before_each=check_cancelled, on_progress=progress)

        result["notifications"]["emails_sent"] = sent
        result["notifications"]["emails_failed"] = failed

        print(f"Emails sent: {sent}", flush=True)
        print(f"Emails failed: {failed}", flush=True)

    except SyncCancelled:
        raise
    except Exception as exc:
        result["error_message"] = (
            f"Notification email processing failed: {exc}"
        )

        print(
            result["error_message"],
            file=sys.stderr,
            flush=True,
        )

    save_result(result)


def main() -> None:
    email_processing_failed = False
    os.environ.setdefault("SYNC_RUN_ID", RUN_ID)
    os.environ.setdefault("SYNC_JOB_ID", RUN_ID)
    with engine.connect() as connection:
        acquired = connection.execute(
            text("SELECT pg_try_advisory_lock(:lock_id)"),
            {"lock_id": SYNC_LOCK_ID},
        ).scalar_one()

        connection.commit()

        if not acquired:
            notify_parent("BUSY")
            print(
                "SYNC ALREADY RUNNING",
                flush=True,
            )
            raise SystemExit(2)

        print("SYNC LOCK ACQUIRED", flush=True)

        result = initial_result()
        started = time.monotonic()

        save_result(result)
        notify_parent("ACQUIRED")

        try:
            run_all_syncs(result)
            if result["datasets"]["failed"]:
                failures = [detail.get("error_message", name) for name, detail in result["dataset_results"].items() if detail["status"] == "failed"]
                raise SystemExit("\n".join(failures) + "\nNotifications remain pending until this job is resumed successfully.")
            check_cancelled()
            result["current_dataset"] = "notifications"
            save_result(result)
            send_notification_emails(result)
            check_cancelled()

            result["status"] = "failed" if result["datasets"]["failed"] else (
                "completed_with_email_errors" if result["notifications"]["emails_failed"] or result["error_message"] else "completed"
            )
            email_processing_failed = result["status"] == "completed_with_email_errors"
            if result["datasets"]["failed"]:
                raise SystemExit(1)

        except SyncCancelled as exc:
            result["status"] = "cancelled"
            result["error_message"] = str(exc)
            connection.execute(text(
                "UPDATE sync_checkpoints SET status = 'cancelled', "
                "error_message = :message WHERE status = 'running'"
            ), {"message": str(exc)})
            connection.commit()

        except BaseException as exc:
            result["status"] = "failed"

            if result["error_message"] is None:
                result["error_message"] = str(exc)

            raise

        finally:
            result["finished_at"] = now_iso()
            result["duration_seconds"] = round(
                time.monotonic() - started,
                2,
            )

            save_result(result)
            CANCEL_FILE.unlink(missing_ok=True)

            connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": SYNC_LOCK_ID},
            )
            connection.commit()

            print("SYNC LOCK RELEASED", flush=True)

    if email_processing_failed:
        # Preserve the detailed run status, but do not tell the scheduler/CLI
        # that a run with failed email delivery completed successfully.
        raise SystemExit("Datasets completed, but email delivery failed. See the run report; notifications remain pending.")


if __name__ == "__main__":
    main()
