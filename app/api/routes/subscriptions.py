from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import SUBSCRIPTION_CHANGE_PER_USER, limiter
from app.db.database import get_db
from app.models.classification import ClassificationCategory
from app.models.monitoring_subscription import UserRecordWatch
from app.models.subscription_profile import MAX_PROFILES_PER_USER, SubscriptionProfile
from app.models.user import User
from app.services.canton_service import CANTON_NAMES
from app.services.email_service import EmailServiceError, send_email
from app.services.entity_registry import ENTITIES


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/subscriptions",
    tags=["Subscriptions"],
)


class ProfileInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    active: bool = True
    category_ids: list[int] = Field(default_factory=list, max_length=100)
    canton_keys: list[str] = Field(default_factory=list, max_length=30)
    keywords: list[str] = Field(default_factory=list, max_length=20)
    datasets: list[str] = Field(default_factory=list, max_length=len(ENTITIES))
    affair_types: list[str] = Field(default_factory=list, max_length=30)


class ProfileOutput(BaseModel):
    id: int
    name: str
    active: bool
    category_ids: list[int]
    canton_keys: list[str]
    keywords: list[str]
    datasets: list[str]
    affair_types: list[str]
    category_names: list[str]
    canton_names: list[str]
    paused: bool


class Watch(BaseModel):
    dataset: str
    record_id: int


class SubscriptionOverview(BaseModel):
    profiles: list[ProfileOutput]
    watches: list[Watch]
    active: bool
    max_profiles: int = MAX_PROFILES_PER_USER


def category_name(category: ClassificationCategory) -> str:
    return category.name_de or category.name_fr or category.code


def send_subscription_email(*, email: str, subject: str, body: str) -> None:
    # Confirmations are informational: past the limit the change is still
    # saved, but no further email is sent to avoid flooding the mailbox.
    if settings.rate_limit_enabled and limiter.hit(
        f"subscription-mail:{email}", SUBSCRIPTION_CHANGE_PER_USER
    ) is not None:
        logger.warning("Subscription confirmation skipped by rate limit.")
        return
    try:
        send_email(recipient=email, subject=subject, body=body)
    except EmailServiceError:
        logger.exception("Subscription email could not be sent.")


def require_verified(user: User) -> None:
    if not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Email verification required.")


def clean_profile(db: Session, payload: ProfileInput) -> dict:
    """Normalise and validate a profile; raise 422/404 for invalid values."""
    name = " ".join(payload.name.split())
    if not name:
        raise HTTPException(422, "The profile name must not be empty.")
    keywords = sorted({" ".join(keyword.split()).casefold() for keyword in payload.keywords})
    if any(not keyword or len(keyword) > 200 for keyword in keywords):
        raise HTTPException(422, "Keywords must contain 1 to 200 characters.")
    datasets = sorted(set(payload.datasets))
    if set(datasets) - set(ENTITIES):
        raise HTTPException(422, "Invalid datasets.")
    cantons = sorted({key.strip().upper() for key in payload.canton_keys})
    invalid_cantons = set(cantons) - set(CANTON_NAMES)
    if invalid_cantons:
        raise HTTPException(422, "Invalid canton codes: " + ", ".join(sorted(invalid_cantons)))
    affair_types = sorted({" ".join(value.split()) for value in payload.affair_types})
    if any(not value or len(value) > 100 for value in affair_types):
        raise HTTPException(422, "Affair types must contain 1 to 100 characters.")
    category_ids = sorted(set(payload.category_ids))
    if any(category_id <= 0 for category_id in category_ids):
        raise HTTPException(422, "Category IDs must be positive.")
    if category_ids:
        found = db.scalars(select(ClassificationCategory).where(
            ClassificationCategory.id.in_(category_ids), ClassificationCategory.active.is_(True))).all()
        if len(found) != len(category_ids):
            raise HTTPException(404, "One or more active categories were not found.")
    return dict(name=name, active=payload.active, category_ids=category_ids, canton_keys=cantons,
                keywords=keywords, datasets=datasets, affair_types=affair_types)


def profile_output(db: Session, profile: SubscriptionProfile) -> ProfileOutput:
    categories = {category.id: category for category in db.scalars(select(ClassificationCategory).where(
        ClassificationCategory.id.in_(profile.category_ids or [])))} if profile.category_ids else {}
    return ProfileOutput(
        id=profile.id, name=profile.name, active=profile.active,
        category_ids=list(profile.category_ids or []), canton_keys=list(profile.canton_keys or []),
        keywords=list(profile.keywords or []), datasets=list(profile.datasets or []),
        affair_types=list(profile.affair_types or []),
        category_names=[category_name(categories[i]) for i in profile.category_ids or [] if i in categories],
        canton_names=[CANTON_NAMES.get(key, key) for key in profile.canton_keys or []],
        paused=not profile.active or not profile.has_filters,
    )


def profile_summary(profile: ProfileOutput) -> str:
    def line(label, values, empty):
        return f"{label}: {', '.join(values) if values else empty}"

    return "\n".join([
        f"«{profile.name}» – {'pausiert' if profile.paused else 'aktiv'}",
        line("Themen", profile.category_names, "alle Themen"),
        line("Kantone", profile.canton_names, "alle Kantone"),
        line("Geschäftstypen", profile.affair_types, "alle Geschäftstypen"),
        line("Suchbegriffe", profile.keywords, "keine Einschränkung"),
        line("Bereiche", profile.datasets, "alle Bereiche"),
    ])


def confirm(user: User, subject: str, intro: str, profile: ProfileOutput | None = None) -> None:
    details = f"{profile_summary(profile)}\n\n" if profile else ""
    send_subscription_email(
        email=user.email,
        subject=f"WWF Polit-Assistant – {subject}",
        body=(
            "Hallo,\n\n"
            f"{intro}\n\n"
            f"{details}"
            "Ein ausgewähltes Oberthema umfasst alle Unterthemen. Mehrere Werte eines Filters gelten "
            "als Alternativen; verschiedene Filter müssen gemeinsam passen. Ein Abonnement ohne Themen, "
            "Kantone, Geschäftstypen und Suchbegriffe ist pausiert.\n\n"
            "Du kannst deine Abonnements jederzeit in der Anwendung verwalten.\n\n"
            "Beste Grüsse\n"
            "WWF Polit-Assistant"
        ),
    )


def own_profile(db: Session, user: User, profile_id: int) -> SubscriptionProfile:
    profile = db.get(SubscriptionProfile, profile_id)
    if profile is None or profile.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subscription not found.")
    return profile


@router.get("", response_model=SubscriptionOverview)
def subscription_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profiles = db.scalars(select(SubscriptionProfile).where(SubscriptionProfile.user_id == current_user.id)
                          .order_by(SubscriptionProfile.id)).all()
    watches = db.scalars(select(UserRecordWatch).where(UserRecordWatch.user_id == current_user.id)).all()
    outputs = [profile_output(db, profile) for profile in profiles]
    return SubscriptionOverview(
        profiles=outputs,
        watches=[Watch(dataset=watch.dataset, record_id=watch.record_id) for watch in watches],
        active=bool(watches) or any(not profile.paused for profile in outputs),
    )


@router.post("/profiles", response_model=ProfileOutput, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_verified(current_user)
    count = len(db.scalars(select(SubscriptionProfile.id).where(SubscriptionProfile.user_id == current_user.id)).all())
    if count >= MAX_PROFILES_PER_USER:
        raise HTTPException(status.HTTP_409_CONFLICT, f"At most {MAX_PROFILES_PER_USER} subscriptions are possible.")
    profile = SubscriptionProfile(user_id=current_user.id, **clean_profile(db, payload))
    db.add(profile)
    db.commit()
    output = profile_output(db, profile)
    confirm(current_user, "Abonnement eingerichtet", "Dein Abonnement wurde gespeichert.", output)
    return output


@router.put("/profiles/{profile_id}", response_model=ProfileOutput)
def update_profile(profile_id: int, payload: ProfileInput, current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    require_verified(current_user)
    profile = own_profile(db, current_user, profile_id)
    for field, value in clean_profile(db, payload).items():
        setattr(profile, field, value)
    db.commit()
    output = profile_output(db, profile)
    confirm(current_user, "Abonnement aktualisiert", "Dein Abonnement wurde geändert.", output)
    return output


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = own_profile(db, current_user, profile_id)
    name = profile.name
    db.delete(profile)
    db.commit()
    confirm(current_user, "Abonnement beendet", f"Dein Abonnement «{name}» wurde gelöscht.")


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def stop_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete every subscription profile and record watch of the account."""
    for model in (SubscriptionProfile, UserRecordWatch):
        db.query(model).filter(model.user_id == current_user.id).delete(synchronize_session=False)
    db.commit()
    confirm(current_user, "Alle Benachrichtigungen beendet",
            "Alle Abonnements und verfolgten Inhalte wurden entfernt. Es werden keine Benachrichtigungen mehr versendet.")


@router.put("/watches/{dataset}/{record_id}", status_code=201)
def watch_record(dataset: str, record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_verified(current_user)
    if dataset not in ENTITIES or record_id <= 0:
        raise HTTPException(422, "Invalid record reference.")
    if db.get(ENTITIES[dataset].model, record_id) is None:
        raise HTTPException(404, "Record not found.")
    key = (current_user.id, dataset, record_id)
    if db.get(UserRecordWatch, key) is None:
        db.add(UserRecordWatch(user_id=current_user.id, dataset=dataset, record_id=record_id))
        db.commit()
    return {"dataset": dataset, "record_id": record_id}


@router.delete("/watches/{dataset}/{record_id}", status_code=204)
def unwatch_record(dataset: str, record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    watch = db.get(UserRecordWatch, (current_user.id, dataset, record_id))
    if watch is not None:
        db.delete(watch)
        db.commit()
