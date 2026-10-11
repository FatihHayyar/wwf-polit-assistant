"""Re-evaluate queued notifications, retaining events and an audit of cancellations."""
import argparse
import json
import uuid
from pathlib import Path

from sqlalchemy import select, text
from app.db.database import SessionLocal
from app.models.change_event import ChangeEvent
from app.models.notification import Notification
from app.services.notification_policy import VERSION, event_eligible


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--apply",action="store_true");args=parser.parse_args()
    with SessionLocal() as db:
        if not db.scalar(text("SELECT pg_try_advisory_xact_lock(:id)"),{"id":2026100801}):
            raise RuntimeError("A sync is running; policy repair not applied.")
        rows=db.execute(select(Notification,ChangeEvent).join(ChangeEvent,ChangeEvent.id==Notification.change_event_id)
                        .where(Notification.status=="pending")).all()
        cancelled=[{"notification_id":n.id,"event_id":e.id,"dataset":e.dataset,"description":e.description,"previous_status":n.status}
                   for n,e in rows if not event_eligible(e)]
        print(json.dumps({"pending":len(rows),"cancel_candidates":len(cancelled),"remain":len(rows)-len(cancelled),"apply":args.apply}))
        if not args.apply:return
        root=Path(__file__).resolve().parents[1]/"logs";root.mkdir(exist_ok=True)
        audit=root/f"notification_policy_audit_{uuid.uuid4().hex}.json"
        audit.write_text(json.dumps({"version":VERSION,"cancellations":cancelled},ensure_ascii=False,indent=2),encoding="utf-8")
        for notification,event in rows:
            event.notification_eligible=event_eligible(event);event.notification_policy=VERSION
            if not event.notification_eligible:
                notification.status="cancelled";notification.error_message="Technical/formatting-only change under meaningful-v1 policy."
        db.commit();print("Audit:",audit.name)


if __name__=="__main__":main()
