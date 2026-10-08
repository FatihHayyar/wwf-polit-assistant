
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.change_event import ChangeEvent
from app.services.notification_service import create_notifications_for_event


def create_change_event(
    db: Session,
    *,
    affair_id: int,
    change_type: str,
    fingerprint: str,
    description: str | None = None,
) -> ChangeEvent:
    """
    Record an affair change and create matching notifications.

    The caller is responsible for committing or rolling back.
    """

    if change_type not in {"created", "updated"}:
        raise ValueError(
            "change_type must be 'created' or 'updated'."
        )

    existing = (
        db.query(ChangeEvent)
        .filter(
            ChangeEvent.dataset == "affairs",
            ChangeEvent.source_id == affair_id,
            ChangeEvent.change_type == change_type,
            ChangeEvent.fingerprint == fingerprint,
        )
        .first()
    )

    if existing is not None:
        return existing

    event = ChangeEvent(
        dataset="affairs",
        source_id=affair_id,
        affair_id=affair_id,
        change_type=change_type,
        fingerprint=fingerprint,
        description=description,
    )

    db.add(event)
    db.flush()

    create_notifications_for_event(db, event)

    return event
