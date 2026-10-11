
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.change_event import ChangeEvent
from app.models.classification import (
    AffairClassification,
    ClassificationCategory,
)
from app.models.notification import Notification
from app.models.user import User


def get_category_and_ancestor_ids(
    db: Session,
    affair_id: int,
) -> set[int]:
    """
    Return directly classified categories and all ancestors.

    A subscription to a parent theme therefore matches
    any affair classified under its child themes.
    """

    direct_category_ids = set(
        db.scalars(
            select(AffairClassification.category_id).where(
                AffairClassification.affair_id == affair_id
            )
        ).all()
    )

    all_category_ids = set(direct_category_ids)
    pending_ids = set(direct_category_ids)

    while pending_ids:
        rows = db.execute(
            select(
                ClassificationCategory.id,
                ClassificationCategory.parent_id,
            ).where(
                ClassificationCategory.id.in_(pending_ids)
            )
        ).all()

        next_pending: set[int] = set()

        for _, parent_id in rows:
            if parent_id is not None and parent_id not in all_category_ids:
                all_category_ids.add(parent_id)
                next_pending.add(parent_id)

        pending_ids = next_pending

    return all_category_ids


def create_notifications_for_event(db: Session, event: ChangeEvent) -> int:
    from app.services.notification_policy import event_eligible
    if not event_eligible(event):
        return 0
    from app.services.monitoring_match_service import event_subjects, matching_subject
    subjects = event_subjects(db, event)
    if not subjects:
        return 0
    existing = set(db.scalars(select(Notification.user_id).where(Notification.change_event_id == event.id)))
    users = db.scalars(select(User.id).where(User.is_active.is_(True), User.email_verified.is_(True)))
    count = 0
    for user_id in users:
        if user_id not in existing and matching_subject(db, user_id, event.dataset, subjects) is not None:
            db.add(Notification(user_id=user_id, change_event_id=event.id, status="pending"))
            count += 1
    db.flush()
    return count
