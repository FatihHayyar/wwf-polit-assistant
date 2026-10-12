"""Complete the failed Events stage and reconcile Documents, without sending mail."""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from app.db.database import engine
from scripts.sync.entity_sync import run_dataset
from scripts.sync.run_all import SYNC_LOCK_ID


def main():
    job_id = os.environ.setdefault("SYNC_JOB_ID", uuid.uuid4().hex)
    os.environ.setdefault("SYNC_RUN_ID", job_id)
    path = Path("logs") / f"repair_{job_id}.json"
    result = {"job_id": job_id, "process_id": os.getpid(), "started_at": datetime.now(timezone.utc).isoformat(), "status": "running", "datasets": {}}
    def save():
        path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    with engine.connect() as connection:
        locked = connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": SYNC_LOCK_ID})
        connection.commit()
        if not locked:
            raise SystemExit("Another synchronization is running; no changes made.")
        try:
            save()
            for dataset in ("documents", "events"):
                print("REPAIR:", dataset, flush=True)
                run_dataset(dataset, backfill_missing_classifications=False)
                result["datasets"][dataset] = dict(connection.execute(text("SELECT status,records_new,records_changed,records_unchanged,records_error FROM sync_checkpoints WHERE dataset=:dataset"), {"dataset": "docs" if dataset == "documents" else dataset}).mappings().one())
                connection.commit()
                save()
            result["status"] = "completed"
        except BaseException as exc:
            result["status"] = "failed"
            result["error"] = str(exc)
            raise
        finally:
            result["finished_at"] = datetime.now(timezone.utc).isoformat()
            save()
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": SYNC_LOCK_ID})
            connection.commit()
            print("REPAIR LOCK RELEASED. Notifications remain pending.", flush=True)


if __name__ == "__main__":
    main()
