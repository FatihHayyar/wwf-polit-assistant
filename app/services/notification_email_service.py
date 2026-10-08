from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.change_event import ChangeEvent
from app.models.entities import Affair, Body
from app.models.notification import Notification
from app.models.subscription import (
    UserCategorySubscription,
    UserCantonSubscription,
)
from app.models.user import User
from app.services.email_service import (
    EmailServiceError,
    send_email,
)
from app.services.notification_service import (
    get_category_and_ancestor_ids,
)


def user_still_subscribed(db, user_id: int, affair: Affair) -> bool:
    category_ids = set(
        db.scalars(
            select(UserCategorySubscription.category_id).where(
                UserCategorySubscription.user_id == user_id
            )
        ).all()
    )

    canton_keys = set(
        db.scalars(
            select(UserCantonSubscription.canton_key).where(
                UserCantonSubscription.user_id == user_id
            )
        ).all()
    )

    # Both empty means no active notification subscription.
    if not category_ids and not canton_keys:
        return False

    # Empty category selection means all themes.
    if category_ids:
        affair_category_ids = get_category_and_ancestor_ids(
            db,
            affair.id,
        )

        if not category_ids.intersection(affair_category_ids):
            return False

    # Empty canton selection means all cantons.
    if canton_keys:
        if affair.body_id is None:
            return False

        canton_key = db.scalar(
            select(Body.canton_key).where(
                Body.id == affair.body_id
            )
        )

        if (
            canton_key is None
            or canton_key.strip().upper() not in canton_keys
        ):
            return False

    return True


def send_pending_notifications(
    *,
    limit: int = 100,
) -> tuple[int, int]:
    """
    Send pending notification emails.

    Returns (sent_count, failed_count).

    Failed notifications remain pending for retry.
    Cancelled notifications are not sent.
    """

    if limit < 1:
        raise ValueError("limit must be positive")

    sent_count = 0
    failed_count = 0

    with SessionLocal() as db:
        notification_ids = db.scalars(
            select(Notification.id)
            .where(Notification.status == "pending")
            .order_by(Notification.created_at, Notification.id)
            .limit(limit)
        ).all()

    for notification_id in notification_ids:
        with SessionLocal() as db:
            notification = db.get(Notification, notification_id)

            if (
                notification is None
                or notification.status != "pending"
            ):
                continue

            user = db.get(User, notification.user_id)
            event = db.get(
                ChangeEvent,
                notification.change_event_id,
            )

            if (
                user is None
                or not user.is_active
                or not user.email_verified
                or event is None
                or event.affair_id is None
            ):
                notification.status = "cancelled"
                db.commit()
                continue

            affair = db.get(Affair, event.affair_id)

            if affair is None:
                notification.status = "cancelled"
                db.commit()
                continue

            # Recheck the user's current subscriptions before sending.
            if not user_still_subscribed(db, user.id, affair):
                notification.status = "cancelled"
                db.commit()
                continue

            title = (
                affair.title_de
                or affair.title_fr
                or affair.title_it
                or affair.title_rm
                or f"Affair {affair.id}"
            )

            action = (
                "New political affair"
                if event.change_type == "created"
                else "Political affair updated"
            )

            body = (
                f"{action}\n\n"
                f"{title}\n\n"
                f"Affair ID: {affair.id}\n"
            )

            try:
                send_email(
                    recipient=user.email,
                    subject=f"WWF Polit-Assistant: {action}",
                    body=body,
                )
            except EmailServiceError as exc:
                notification.error_message = str(exc)
                db.commit()
                failed_count += 1
                continue

            notification.status = "sent"
            notification.sent_at = datetime.now(timezone.utc)
            notification.error_message = None
            db.commit()

            sent_count += 1

    return sent_count, failed_count