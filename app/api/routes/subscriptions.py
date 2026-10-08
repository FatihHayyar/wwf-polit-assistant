
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.classification import ClassificationCategory
from app.models.subscription import (
    UserCantonSubscription,
    UserCategorySubscription,
)
from app.models.user import User
from app.services.canton_service import CANTON_NAMES
from app.services.email_service import EmailServiceError, send_email


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/subscriptions",
    tags=["Subscriptions"],
)


class CategorySubscriptionCreate(BaseModel):
    category_id: int = Field(gt=0)


class CategorySubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    created_at: datetime


class CantonSubscriptionCreate(BaseModel):
    canton_key: str = Field(min_length=2, max_length=20)


class CantonSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canton_key: str
    created_at: datetime


class SubscriptionUpdate(BaseModel):
    category_ids: list[int] = Field(default_factory=list)
    canton_keys: list[str] = Field(default_factory=list)


class SubscriptionSummary(BaseModel):
    category_ids: list[int]
    canton_keys: list[str]
    all_categories: bool
    all_cantons: bool
    category_names: list[str]
    canton_names: list[str]


def category_name(category: ClassificationCategory) -> str:
    return (
        category.name_de
        or category.name_fr
        or category.code
    )


def send_subscription_email(
    *,
    email: str,
    subject: str,
    body: str,
) -> None:
    try:
        send_email(
            recipient=email,
            subject=subject,
            body=body,
        )
    except EmailServiceError:
        logger.exception(
            "Subscription email could not be sent."
        )


def send_single_subscription_confirmation(
    *,
    email: str,
    action: str,
    subscription_type: str,
    subscription_name: str,
) -> None:
    if action == "created":
        subject = "WWF Polit-Assistant – Abonnement bestätigt"
        message = "Dein Abonnement wurde erfolgreich eingerichtet."
    else:
        subject = "WWF Polit-Assistant – Abonnement beendet"
        message = "Dein Abonnement wurde erfolgreich beendet."

    send_subscription_email(
        email=email,
        subject=subject,
        body=(
            "Hallo,\n\n"
            f"{message}\n\n"
            f"Bereich: {subscription_type}\n"
            f"Auswahl: {subscription_name}\n\n"
            "Du kannst deine Abonnements jederzeit "
            "in den Einstellungen verwalten.\n\n"
            "Beste Grüsse\n"
            "WWF Polit-Assistant"
        ),
    )


@router.put(
    "",
    response_model=SubscriptionSummary,
)
def update_all_subscriptions(
    payload: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email verification required.",
        )

    requested_category_ids = set(payload.category_ids)

    if any(
        category_id <= 0
        for category_id in requested_category_ids
    ):
        raise HTTPException(
            status_code=422,
            detail="Category IDs must be positive.",
        )

    normalized_cantons = {
        key.strip().upper()
        for key in payload.canton_keys
    }

    invalid_cantons = normalized_cantons - set(CANTON_NAMES)

    if invalid_cantons:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid canton codes: "
                + ", ".join(sorted(invalid_cantons))
            ),
        )

    # At least one theme or canton must be selected.
    if not requested_category_ids and not normalized_cantons:
        raise HTTPException(
            status_code=422,
            detail=(
                "Select at least one category or canton. "
                "An empty group means all values in that group."
            ),
        )

    categories = (
        db.query(ClassificationCategory)
        .filter(
            ClassificationCategory.id.in_(
                requested_category_ids
            )
        )
        .all()
        if requested_category_ids
        else []
    )

    if (
        len(categories) != len(requested_category_ids)
        or any(not category.active for category in categories)
    ):
        raise HTTPException(
            status_code=404,
            detail="One or more active categories were not found.",
        )

    existing_categories = (
        db.query(UserCategorySubscription)
        .filter(
            UserCategorySubscription.user_id == current_user.id
        )
        .all()
    )

    existing_cantons = (
        db.query(UserCantonSubscription)
        .filter(
            UserCantonSubscription.user_id == current_user.id
        )
        .all()
    )

    existing_category_ids = {
        item.category_id for item in existing_categories
    }

    existing_canton_keys = {
        item.canton_key for item in existing_cantons
    }

    # Replace category subscriptions.
    for item in existing_categories:
        if item.category_id not in requested_category_ids:
            db.delete(item)

    for category_id in requested_category_ids - existing_category_ids:
        db.add(
            UserCategorySubscription(
                user_id=current_user.id,
                category_id=category_id,
            )
        )

    # Replace canton subscriptions.
    for item in existing_cantons:
        if item.canton_key not in normalized_cantons:
            db.delete(item)

    for canton_key in normalized_cantons - existing_canton_keys:
        db.add(
            UserCantonSubscription(
                user_id=current_user.id,
                canton_key=canton_key,
            )
        )

    db.commit()

    sorted_categories = sorted(
        categories,
        key=lambda category: category.id,
    )

    sorted_cantons = sorted(normalized_cantons)

    selected_category_names = (
        [category_name(category) for category in sorted_categories]
        if sorted_categories
        else ["Alle Themen"]
    )

    selected_canton_names = (
        [CANTON_NAMES[key] for key in sorted_cantons]
        if sorted_cantons
        else ["Alle Kantone"]
    )

    theme_lines = "\n".join(
        f"- {name}" for name in selected_category_names
    )

    canton_lines = "\n".join(
        f"- {name}" for name in selected_canton_names
    )

    send_subscription_email(
        email=current_user.email,
        subject="WWF Polit-Assistant – Abonnements aktualisiert",
        body=(
            "Hallo,\n\n"
            "Deine Abonnements wurden erfolgreich gespeichert.\n\n"
            "Deine abonnierten Themen:\n"
            f"{theme_lines}\n\n"
            "Deine Kantone:\n"
            f"{canton_lines}\n\n"
            "Ein ausgewähltes Oberthema umfasst alle Unterthemen.\n"
            "Wenn keine Themen ausgewählt sind, gelten alle Themen.\n"
            "Wenn keine Kantone ausgewählt sind, gelten alle Kantone.\n\n"
            "Beste Grüsse\n"
            "WWF Polit-Assistant"
        ),
    )

    return SubscriptionSummary(
        category_ids=sorted(requested_category_ids),
        canton_keys=sorted_cantons,
        all_categories=not bool(requested_category_ids),
        all_cantons=not bool(sorted_cantons),
        category_names=selected_category_names,
        canton_names=selected_canton_names,
    )


@router.get(
    "/categories",
    response_model=list[CategorySubscriptionResponse],
)
def list_category_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(UserCategorySubscription)
        .filter(
            UserCategorySubscription.user_id == current_user.id
        )
        .order_by(UserCategorySubscription.id)
        .all()
    )


@router.post(
    "/categories",
    response_model=CategorySubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category_subscription(
    payload: CategorySubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email verification required.",
        )

    category = db.get(ClassificationCategory, payload.category_id)

    if category is None or not category.active:
        raise HTTPException(
            status_code=404,
            detail="Active category not found.",
        )

    existing = (
        db.query(UserCategorySubscription)
        .filter(
            UserCategorySubscription.user_id == current_user.id,
            UserCategorySubscription.category_id == payload.category_id,
        )
        .first()
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Already subscribed to this category.",
        )

    subscription = UserCategorySubscription(
        user_id=current_user.id,
        category_id=payload.category_id,
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    send_single_subscription_confirmation(
        email=current_user.email,
        action="created",
        subscription_type="Thema",
        subscription_name=category_name(category),
    )

    return subscription


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category_subscription(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscription = (
        db.query(UserCategorySubscription)
        .filter(
            UserCategorySubscription.user_id == current_user.id,
            UserCategorySubscription.category_id == category_id,
        )
        .first()
    )

    if subscription is None:
        raise HTTPException(
            status_code=404,
            detail="Category subscription not found.",
        )

    category = db.get(ClassificationCategory, category_id)

    name = (
        category_name(category)
        if category is not None
        else str(category_id)
    )

    db.delete(subscription)
    db.commit()

    send_single_subscription_confirmation(
        email=current_user.email,
        action="deleted",
        subscription_type="Thema",
        subscription_name=name,
    )


@router.get(
    "/cantons",
    response_model=list[CantonSubscriptionResponse],
)
def list_canton_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(UserCantonSubscription)
        .filter(
            UserCantonSubscription.user_id == current_user.id
        )
        .order_by(UserCantonSubscription.canton_key)
        .all()
    )


@router.post(
    "/cantons",
    response_model=CantonSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_canton_subscription(
    payload: CantonSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email verification required.",
        )

    canton_key = payload.canton_key.strip().upper()

    if canton_key not in CANTON_NAMES:
        raise HTTPException(
            status_code=404,
            detail="Invalid canton code.",
        )

    existing = (
        db.query(UserCantonSubscription)
        .filter(
            UserCantonSubscription.user_id == current_user.id,
            UserCantonSubscription.canton_key == canton_key,
        )
        .first()
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Already subscribed to this canton.",
        )

    subscription = UserCantonSubscription(
        user_id=current_user.id,
        canton_key=canton_key,
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    send_single_subscription_confirmation(
        email=current_user.email,
        action="created",
        subscription_type="Kanton",
        subscription_name=CANTON_NAMES[canton_key],
    )

    return subscription


@router.delete(
    "/cantons/{canton_key}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_canton_subscription(
    canton_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    normalized_key = canton_key.strip().upper()

    subscription = (
        db.query(UserCantonSubscription)
        .filter(
            UserCantonSubscription.user_id == current_user.id,
            UserCantonSubscription.canton_key == normalized_key,
        )
        .first()
    )

    if subscription is None:
        raise HTTPException(
            status_code=404,
            detail="Canton subscription not found.",
        )

    db.delete(subscription)
    db.commit()

    send_single_subscription_confirmation(
        email=current_user.email,
        action="deleted",
        subscription_type="Kanton",
        subscription_name=CANTON_NAMES.get(
            normalized_key,
            normalized_key,
        ),
    )
