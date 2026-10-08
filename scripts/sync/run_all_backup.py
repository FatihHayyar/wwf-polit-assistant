
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

from app.db.database import engine


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


def notify_parent(message: str) -> None:
    """Write the startup result for the API, if requested."""
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


def run_all_syncs() -> bool:
    started_at = datetime.now()
    total = len(SYNC_MODULES)
    completed = []

    print("=" * 70, flush=True)
    print("WWF POLIT-ASSISTANT - ALL DATASET SYNC", flush=True)
    print("=" * 70, flush=True)
    print(f"Start: {started_at}", flush=True)
    print(f"Datasets: {total}", flush=True)

    for index, (name, module) in enumerate(
        SYNC_MODULES,
        start=1,
    ):
        print("\n" + "=" * 70, flush=True)
        print(f"[{index}/{total}] START: {name}", flush=True)
        print(f"Module: {module}", flush=True)
        print("=" * 70, flush=True)

        start_time = time.monotonic()

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-u",
                    "-m",
                    module,
                ],
                check=False,
            )
        except KeyboardInterrupt:
            print(f"\nINTERRUPTED: {name}", flush=True)
            raise SystemExit(130)

        duration = time.monotonic() - start_time

        if result.returncode != 0:
            print("\n" + "=" * 70, flush=True)
            print("SYNC FAILED", flush=True)
            print(f"Dataset: {name}", flush=True)
            print(f"Exit code: {result.returncode}", flush=True)
            print(
                f"Completed datasets: {len(completed)}/{total}",
                flush=True,
            )
            print(
                "Remaining datasets were NOT started.",
                flush=True,
            )
            print("=" * 70, flush=True)

            raise SystemExit(result.returncode)

        completed.append(name)

        print(
            f"\n[{index}/{total}] OK: {name} "
            f"({duration:.1f} seconds)",
            flush=True,
        )

    finished_at = datetime.now()

    print("\n" + "=" * 70, flush=True)
    print("ALL DATASET SYNCS COMPLETED", flush=True)
    print("=" * 70, flush=True)
    print(f"Started: {started_at}", flush=True)
    print(f"Finished: {finished_at}", flush=True)
    print(f"Successful: {len(completed)}/{total}", flush=True)
    print("=" * 70, flush=True)

    return True


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
                "SYNC ALREADY RUNNING: "
                "Another sync process holds the lock.",
                flush=True,
            )
            raise SystemExit(2)

        print("SYNC LOCK ACQUIRED", flush=True)
        notify_parent("ACQUIRED")

        try:
            run_all_syncs()
        finally:
            connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": SYNC_LOCK_ID},
            )
            connection.commit()
            print("SYNC LOCK RELEASED", flush=True)


if __name__ == "__main__":
    main()
