
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.change_event import ChangeEvent
from app.models.classification import (
    AffairClassification,
    ClassificationCategory,
)
from app.models.entities import Affair, Body
from app.models.notification import Notification
from app.models.subscription import (
    UserCantonSubscription,
    UserCategorySubscription,
)
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


def create_notifications_for_event(
    db: Session,
    event: ChangeEvent,
) -> int:
    """
    Matching rules:

    Themes:
      - Multiple selected themes use OR.
      - A selected parent includes its descendants.
      - No selected themes means ALL themes.

    Cantons:
      - Multiple selected cantons use OR.
      - No selected cantons means ALL cantons.

    Between groups:
      - Theme match AND canton match are required.

    A user with neither themes nor cantons is excluded.

    Does not send emails or commit the transaction.
    """

    if event.affair_id is None:
        return 0

    affair = db.get(Affair, event.affair_id)

    if affair is None:
        return 0

    # Only active, verified users are eligible.
    eligible_user_ids = set(
        db.scalars(
            select(User.id).where(
                User.is_active.is_(True),
                User.email_verified.is_(True),
            )
        ).all()
    )

    if not eligible_user_ids:
        return 0

    # Users who have explicitly selected themes.
    category_subscribers = set(
        db.scalars(
            select(UserCategorySubscription.user_id).where(
                UserCategorySubscription.user_id.in_(
                    eligible_user_ids
                )
            )
        ).all()
    )

    # Users who have explicitly selected cantons.
    canton_subscribers = set(
        db.scalars(
            select(UserCantonSubscription.user_id).where(
                UserCantonSubscription.user_id.in_(
                    eligible_user_ids
                )
            )
        ).all()
    )

    # Both groups empty means no subscription.
    subscribed_user_ids = (
        category_subscribers | canton_subscribers
    )

    if not subscribed_user_ids:
        return 0

    # Theme matching.
    matching_category_ids = get_category_and_ancestor_ids(
        db,
        affair.id,
    )

    matching_category_user_ids: set[int] = set()

    if matching_category_ids:
        matching_category_user_ids = set(
            db.scalars(
                select(UserCategorySubscription.user_id).where(
                    UserCategorySubscription.category_id.in_(
                        matching_category_ids
                    ),
                    UserCategorySubscription.user_id.in_(
                        subscribed_user_ids
                    ),
                )
            ).all()
        )

    # No theme selection means all themes.
    unrestricted_category_user_ids = (
        subscribed_user_ids - category_subscribers
    )

    theme_matched_user_ids = (
        matching_category_user_ids
        | unrestricted_category_user_ids
    )

    if not theme_matched_user_ids:
        return 0

    # Canton matching.
    canton_key = None

    if affair.body_id is not None:
        canton_key = db.scalar(
            select(Body.canton_key).where(
                Body.id == affair.body_id
            )
        )

    matching_canton_user_ids: set[int] = set()

    if canton_key:
        matching_canton_user_ids = set(
            db.scalars(
                select(UserCantonSubscription.user_id).where(
                    UserCantonSubscription.user_id.in_(
                        theme_matched_user_ids
                    ),
                    UserCantonSubscription.canton_key
                    == canton_key.strip().upper(),
                )
            ).all()
        )

    # No canton selection means all cantons.
    unrestricted_canton_user_ids = (
        theme_matched_user_ids - canton_subscribers
    )

    matched_user_ids = (
        unrestricted_canton_user_ids
        | matching_canton_user_ids
    )

    if not matched_user_ids:
        return 0

    # Avoid duplicate notifications for the same event.
    existing_user_ids = set(
        db.scalars(
            select(Notification.user_id).where(
                Notification.change_event_id == event.id,
                Notification.user_id.in_(matched_user_ids),
            )
        ).all()
    )

    created = 0

    for user_id in matched_user_ids - existing_user_ids:
        db.add(
            Notification(
                user_id=user_id,
                change_event_id=event.id,
                status="pending",
            )
        )
        created += 1

    db.flush()

    return created
