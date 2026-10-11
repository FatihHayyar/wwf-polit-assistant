
from __future__ import annotations
import hashlib

from sqlalchemy.orm import Session

from app.models.change_event import ChangeEvent
from app.models.change_event_affair import ChangeEventAffair
from app.services.notification_service import create_notifications_for_event


SUPPORTED_DATASETS = {
    "affairs",
    "agendas",
    "meetings",
    "votings",
    "events",
    "documents",
    "texts",
    "groups",
    "interests",
}


def create_change_event(
    db: Session,
    *,
    affair_id: int | None = None,
    change_type: str,
    fingerprint: str,
    description: str | None = None,
    dataset: str = "affairs",
    source_id: int | None = None,
    affair_ids: set[int] | None = None,
    new_occurrence: bool = False,
) -> ChangeEvent:
    """
    Record an entity change and create matching notifications.

    The caller is responsible for committing or rolling back.

    Existing Affairs calls remain compatible.
    """

    if dataset not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported dataset: {dataset}")

    if change_type not in {"created", "updated"}:
        raise ValueError(
            "change_type must be 'created' or 'updated'."
        )

    if source_id is None:
        if dataset == "affairs" and affair_id is not None:
            source_id = affair_id
        else:
            raise ValueError(
                "source_id is required for non-Affairs datasets."
            )

    if dataset == "affairs":
        if affair_id is None:
            affair_id = source_id
        elif affair_id != source_id:
            raise ValueError(
                "For Affairs, affair_id must equal source_id."
            )

    if new_occurrence:
        previous = (db.query(ChangeEvent.id).filter(ChangeEvent.dataset == dataset,
                    ChangeEvent.source_id == source_id).order_by(ChangeEvent.id.desc()).first())
        fingerprint = hashlib.sha256(f"{previous[0] if previous else 0}:{fingerprint}".encode()).hexdigest()

    existing = (
        db.query(ChangeEvent)
        .filter(
            ChangeEvent.dataset == dataset,
            ChangeEvent.source_id == source_id,
            ChangeEvent.change_type == change_type,
            ChangeEvent.fingerprint == fingerprint,
        )
        .first()
    )

    affected = set(affair_ids or ())
    if affair_id is not None:
        affected.add(affair_id)
    if existing is not None:
        event = existing
    else:
        event = ChangeEvent(
            dataset=dataset, source_id=source_id, affair_id=affair_id,
            change_type=change_type, fingerprint=fingerprint, description=description,
        )
        db.add(event)
        db.flush()

    for affected_id in affected:
        key = (event.id, affected_id)
        if db.get(ChangeEventAffair, key) is None:
            db.add(ChangeEventAffair(change_event_id=event.id, affair_id=affected_id))
    db.flush()

    create_notifications_for_event(db, event)

    return event
