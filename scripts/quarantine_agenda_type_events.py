"""Quarantine item-number-only events from a cancelled run, preserving an audit copy.

The old event does not store previous values, so a historical real number change
cannot be distinguished from the known type bug. Candidates are retained, not
deleted; changes to any other field and new records are left untouched.
"""
import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, text, update

from app.db.database import SessionLocal
from app.models.change_event import ChangeEvent
from app.models.notification import Notification


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id", type=uuid.UUID)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "logs"
    result = json.loads((root / f"sync_{args.run_id.hex}.json").read_text(encoding="utf-8"))
    if result["status"] != "cancelled":
        raise ValueError("Only a confirmed cancelled run may be repaired.")
    with SessionLocal() as db:
        # Same advisory lock as run_all: repair must not race a new synchronization.
        acquired = db.scalar(text("SELECT pg_try_advisory_xact_lock(:id)"), {"id": 2026100801})
        if not acquired:
            raise RuntimeError("A synchronization is running; repair was not applied.")
        events = db.scalars(select(ChangeEvent).where(
            ChangeEvent.dataset == "agendas", ChangeEvent.change_type == "updated",
            ChangeEvent.description == "Changed fields: item_number",
            ChangeEvent.detected_at >= datetime.fromisoformat(result["started_at"]),
            ChangeEvent.detected_at <= datetime.fromisoformat(result["finished_at"]),
        )).all()
        ids = [event.id for event in events]
        notifications = db.scalars(select(Notification).where(Notification.change_event_id.in_(ids))).all()
        print(json.dumps({"candidate_events": len(ids), "pending_notifications": sum(n.status == "pending" for n in notifications),
                          "sent_notifications": sum(n.status == "sent" for n in notifications), "apply": args.apply}))
        if not args.apply or not ids:
            return
        audit = {"run_id": args.run_id.hex, "reason": "Known API integer/database text mismatch; item_number-only candidates quarantined.",
                 "events": [{c.key: getattr(e, c.key) for c in ChangeEvent.__table__.columns} for e in events],
                 "notifications": [{c.key: getattr(n, c.key) for c in Notification.__table__.columns} for n in notifications]}
        audit_path = root / f"agenda_type_audit_{args.run_id.hex}_{uuid.uuid4().hex}.json"
        audit_path.write_text(json.dumps(audit, default=str, ensure_ascii=False, indent=2), encoding="utf-8")
        db.execute(update(Notification).where(Notification.change_event_id.in_(ids), Notification.status == "pending").values(
            status="cancelled", error_message="Quarantined: item_number type mismatch in cancelled sync."))
        db.execute(update(ChangeEvent).where(ChangeEvent.id.in_(ids)).values(change_type="ignored"))
        db.commit()
        print(f"Audit preserved: {audit_path.name}")


if __name__ == "__main__":
    main()
