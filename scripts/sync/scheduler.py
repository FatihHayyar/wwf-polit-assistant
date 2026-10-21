
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TIMEZONE = ZoneInfo("Europe/Zurich")
# OpenParlData publishes its daily exports around 02:15 UTC (04:15 in summer,
# 03:15 in winter Zurich time). Running afterwards picks up the night's changes
# on the same day instead of one day later.
DEFAULT_SYNC_TIME = "04:30"


def sync_time() -> tuple[int, int]:
    """Daily start time from SYNC_TIME (HH:MM, Europe/Zurich)."""
    value = os.environ.get("SYNC_TIME", DEFAULT_SYNC_TIME).strip()
    hour, _, minute = value.partition(":")
    if not (hour.isdigit() and minute.isdigit() and int(hour) < 24 and int(minute) < 60):
        raise ValueError(f"SYNC_TIME must be HH:MM, got {value!r}.")
    return int(hour), int(minute)


def run_scheduled_sync() -> None:
    print(
        f"[{datetime.now(TIMEZONE).isoformat()}] "
        "Scheduled sync starting...",
        flush=True,
    )

    result = subprocess.run(
        [
            sys.executable,
            "-u",
            "-m",
            "scripts.sync.run_all",
        ],
        cwd=str(PROJECT_ROOT),
        check=False,
    )

    print(
        f"Scheduled sync finished. Exit code: {result.returncode}",
        flush=True,
    )


def create_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone=TIMEZONE)
    hour, minute = sync_time()

    scheduler.add_job(
        run_scheduled_sync,
        trigger=CronTrigger(
            hour=hour,
            minute=minute,
            timezone=TIMEZONE,
        ),
        id="daily_parliamentary_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    return scheduler


def main() -> None:
    scheduler = create_scheduler()

    print("=" * 60, flush=True)
    print("WWF POLIT-ASSISTANT - AUTOMATIC SYNC SCHEDULER", flush=True)
    hour, minute = sync_time()
    print(f"Schedule: Every day at {hour:02d}:{minute:02d} Europe/Zurich", flush=True)
    print(f"Next run: {scheduler.get_job('daily_parliamentary_sync').next_run_time if scheduler.running else 'Available after scheduler starts'}", flush=True)
    print("=" * 60, flush=True)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.", flush=True)


if __name__ == "__main__":
    main()
