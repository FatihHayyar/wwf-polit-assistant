from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from app.db.database import engine
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
]

SYNC_LOCK_ID = 2026100801

RUN_ID = os.environ.get("SYNC_RUN_ID")
RESULT_FILE = os.environ.get("SYNC_RESULT_FILE")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_result(result: dict) -> None:
    if not RESULT_FILE:
        return

    path = Path(RESULT_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(path)


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
    return {
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
    }


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


def update_record_totals(
    result: dict,
    dataset_name: str,
) -> None:
    dataset_key = {
        "Affairs": "affairs",
        "Agendas": "agendas",
        "Meetings": "meetings",
        "Votings": "votings",
        "Events": "events",
        "Documents": "docs",
        "Texts": "texts",
    }[dataset_name]

    snapshot = checkpoint_snapshot()
    counts = snapshot.get(dataset_key)

    if counts is None:
        return

    for key in ("new", "changed", "unchanged", "errors"):
        result["records"][key] += counts[key]


def run_all_syncs(result: dict) -> None:
    started_at = datetime.now()
    total = len(SYNC_MODULES)

    print("=" * 70, flush=True)
    print("WWF POLIT-ASSISTANT - ALL DATASET SYNC", flush=True)
    print("=" * 70, flush=True)
    print(f"Start: {started_at}", flush=True)
    print(f"Datasets: {total}", flush=True)

    for index, (name, module) in enumerate(SYNC_MODULES, start=1):
        print("\n" + "=" * 70, flush=True)
        print(f"[{index}/{total}] START: {name}", flush=True)
        print(f"Module: {module}", flush=True)
        print("=" * 70, flush=True)

        start_time = time.monotonic()

        try:
            process = subprocess.run(
                [sys.executable, "-u", "-m", module],
                check=False,
            )
        except KeyboardInterrupt:
            raise SystemExit(130)

        duration = time.monotonic() - start_time

        if process.returncode != 0:
            result["datasets"]["failed"] += 1
            result["error_message"] = (
                f"{name} sync failed "
                f"(exit code {process.returncode})."
            )
            save_result(result)

            print(
                f"SYNC FAILED: {name} "
                f"(exit code {process.returncode})",
                flush=True,
            )

            raise SystemExit(process.returncode)

        result["datasets"]["successful"] += 1

        update_record_totals(result, name)
        save_result(result)

        print(
            f"\n[{index}/{total}] OK: {name} "
            f"({duration:.1f} seconds)",
            flush=True,
        )

    print("\n" + "=" * 70, flush=True)
    print("ALL DATASET SYNCS COMPLETED", flush=True)
    print(
        f"Successful: "
        f"{result['datasets']['successful']}/{total}",
        flush=True,
    )


def send_notification_emails(result: dict) -> None:
    print("\n" + "=" * 70, flush=True)
    print("SENDING PENDING NOTIFICATION EMAILS", flush=True)
    print("=" * 70, flush=True)

    try:
        sent, failed = send_pending_notifications(limit=100)

        result["notifications"]["emails_sent"] = sent
        result["notifications"]["emails_failed"] = failed

        print(f"Emails sent: {sent}", flush=True)
        print(f"Emails failed: {failed}", flush=True)

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
            send_notification_emails(result)

            result["status"] = "completed"

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

            connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": SYNC_LOCK_ID},
            )
            connection.commit()

            print("SYNC LOCK RELEASED", flush=True)


if __name__ == "__main__":
    main()