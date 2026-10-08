
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime


SYNC_MODULES = [
    ("Affairs", "scripts.sync.incremental_sync"),
    ("Agendas", "scripts.sync.agendas_sync"),
    ("Meetings", "scripts.sync.meetings_sync"),
    ("Votings", "scripts.sync.votings_sync"),
    ("Events", "scripts.sync.events_sync"),
    ("Documents", "scripts.sync.docs_sync"),
    ("Texts", "scripts.sync.texts_sync"),
]


def main() -> None:
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
        print(
            f"[{index}/{total}] START: {name}",
            flush=True,
        )
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
            print(
                f"\nINTERRUPTED: {name}",
                flush=True,
            )
            raise SystemExit(130)

        duration = time.monotonic() - start_time

        if result.returncode != 0:
            print("\n" + "=" * 70, flush=True)
            print("SYNC FAILED", flush=True)
            print(f"Dataset: {name}", flush=True)
            print(
                f"Exit code: {result.returncode}",
                flush=True,
            )
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


if __name__ == "__main__":
    main()
