
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TIMEZONE = ZoneInfo("Europe/Zurich")


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

    scheduler.add_job(
        run_scheduled_sync,
        trigger=CronTrigger(
            hour=3,
            minute=0,
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
    print("Schedule: Every day at 03:00 Europe/Zurich", flush=True)
    print(f"Next run: {scheduler.get_job('daily_parliamentary_sync').next_run_time if scheduler.running else 'Available after scheduler starts'}", flush=True)
    print("=" * 60, flush=True)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.", flush=True)


if __name__ == "__main__":
    main()
