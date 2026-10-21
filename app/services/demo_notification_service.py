"""Demo-only: create a sample affair and run the real notification pipeline.

The affair passes through the configured rule classifier, the change-event
policy, subscription matching and the email digest, exactly like a record that
arrives through the synchronisation. Only the source data is simulated.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.classification.classifier import CLASSIFIER_VERSION, AffairClassifier, confidence_for_match
from app.models.classification import AffairClassification, ClassificationCategory
from app.models.entities import Affair, Body
from app.models.monitoring_subscription import UserKeywordSubscription
from app.models.notification import Notification
from app.models.subscription import UserCantonSubscription, UserCategorySubscription
from app.models.user import User
from app.services.change_event_service import create_change_event


# Demo records use their own ID range so they never collide with OpenParlData.
DEMO_ID_START = 900_000_000

DEMO_TITLES = {
    "renewable_electricity": "Mehr Photovoltaik auf den Dächern kantonaler Schulhäuser",
    "renewable_heat": "Förderung von Wärmepumpen und Fernwärme in Wohnquartieren",
    "building_efficiency": "Gebäudesanierung: Energieeffizienz der kantonalen Liegenschaften erhöhen",
    "sustainable_mobility": "Ladeinfrastruktur für die Elektromobilität an Bahnhöfen ausbauen",
    "grids_storage": "Netzausbau und Batteriespeicher für die Versorgungssicherheit",
    "fossil_energy": "Ersatz von Ölheizungen und Gasheizungen in öffentlichen Gebäuden",
    "large_consumers_datacenters": "Abwärmenutzung bei Rechenzentren und Grossverbrauchern",
    "climate_energy_other": "Kantonale Strategie zum Klimaschutz bis 2040",
    "species_habitats": "Artenschutz: Biotope für bedrohte Wildtiere vernetzen",
    "protected_areas": "Erweiterung des Naturschutzgebiets am Seeufer",
    "forest": "Waldreservate und Schutzwald langfristig sichern",
    "waters": "Revitalisierung von Fliessgewässern und Gewässerschutz verstärken",
    "soil_spatial_planning": "Bodenversiegelung stoppen und Fruchtfolgeflächen schützen",
    "agriculture_biodiversity": "Weniger Pestizide und mehr Biodiversitätsförderflächen in der Landwirtschaft",
    "biodiversity_landscape_other": "Aktionsplan Biodiversität für den Kanton",
    "circular_economy": "Kreislaufwirtschaft stärken: Recycling und Wiederverwendung von Baustoffen",
    "resources_raw_materials": "Rohstoffverbrauch senken und Ressourceneffizienz in der Verwaltung fördern",
    "sustainable_finance": "Nachhaltige Finanzierung und Green Bonds der Kantonalbank",
    "companies_supply_chains": "Nachhaltigkeitsberichterstattung für Unternehmen mit globalen Lieferketten",
    "food_consumption": "Lebensmittelverschwendung in Kantinen halbieren",
    "sustainable_economy_consumption_other": "Leitbild für eine nachhaltige Wirtschaft im Kanton",
    "environmental_law": "Teilrevision des kantonalen Umweltgesetzes",
    "public_sector": "Nachhaltige Beschaffung nach ökologischen Kriterien beim Kanton und seinen Betrieben",
    "environmental_funding": "Einen Klimafonds für lokale Klimaschutzprojekte schaffen",
    "international_environment": "Umsetzung des Pariser Klimaabkommens auf kantonaler Ebene",
    "environmental_research_education": "Umweltbildung an Volksschulen ausbauen",
    "environment_policy_other": "Bericht zur kantonalen Umweltpolitik",
}


class DemoNotificationError(ValueError):
    """The demo affair cannot be created with the given input."""


@dataclass
class DemoResult:
    affair_id: int
    title: str
    canton: str | None
    categories: list[str]
    notifications_for_user: int
    emails_sent: int = 0
    emails_failed: int = 0
    hints: list[str] = field(default_factory=list)


def demo_category_choices(db: Session, user: User) -> tuple[list[dict], str | None]:
    """Return selectable topics and the one preselected for this user."""
    categories = db.scalars(
        select(ClassificationCategory).where(ClassificationCategory.active.is_(True))
        .order_by(ClassificationCategory.sort_order, ClassificationCategory.id)
    ).all()
    by_id = {category.id: category for category in categories}
    choices = [
        {"code": category.code,
         "name": f"{by_id[category.parent_id].name_de} / {category.name_de}" if category.parent_id in by_id else category.name_de}
        for category in categories if category.code in DEMO_TITLES
    ]
    subscribed = db.scalars(select(UserCategorySubscription.category_id)
                            .where(UserCategorySubscription.user_id == user.id)).all()
    preselected = None
    for category_id in subscribed:
        category = by_id.get(category_id)
        if category is not None:
            leaf = leaf_for(db, category)
            if leaf is not None:
                preselected = leaf.code
                break
    return choices, preselected


def leaf_for(db: Session, category: ClassificationCategory) -> ClassificationCategory | None:
    if category.code in DEMO_TITLES:
        return category
    children = db.scalars(
        select(ClassificationCategory).where(ClassificationCategory.parent_id == category.id,
                                             ClassificationCategory.active.is_(True))
        .order_by(ClassificationCategory.sort_order, ClassificationCategory.id)
    ).all()
    return next((child for child in children if child.code in DEMO_TITLES), None)


def choose_body(db: Session, user: User) -> Body:
    cantons = db.scalars(select(UserCantonSubscription.canton_key)
                         .where(UserCantonSubscription.user_id == user.id)).all()
    query = select(Body).where(Body.canton_key.is_not(None))
    if cantons:
        query = query.where(func.upper(Body.canton_key).in_([key.upper() for key in cantons]))
    body = db.scalars(query.order_by(Body.id).limit(1)).first()
    if body is None:
        raise DemoNotificationError("No parliament body is available for the selected cantons.")
    return body


def next_demo_id(db: Session) -> int:
    current = db.scalar(select(func.max(Affair.id)).where(Affair.id >= DEMO_ID_START))
    return (current or DEMO_ID_START - 1) + 1


def create_demo_affair(db: Session, user: User, category_code: str) -> DemoResult:
    """Insert, classify and announce a demo affair. The caller commits."""
    category = db.scalar(select(ClassificationCategory).where(
        ClassificationCategory.code == category_code, ClassificationCategory.active.is_(True)))
    leaf = leaf_for(db, category) if category is not None else None
    if leaf is None:
        raise DemoNotificationError("Unknown topic for the demo notification.")

    body = choose_body(db, user)
    title = DEMO_TITLES[leaf.code]
    keyword = db.scalars(select(UserKeywordSubscription.keyword)
                         .where(UserKeywordSubscription.user_id == user.id)
                         .order_by(UserKeywordSubscription.keyword).limit(1)).first()
    if keyword and keyword.casefold() not in title.casefold():
        # Keyword filters must match too, so the subscribed phrase is included.
        title = f"{title} ({keyword})"

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    affair_id = next_demo_id(db)
    affair = Affair(
        id=affair_id, body_id=body.id, body_key=body.body_key,
        number=f"DEMO-{affair_id - DEMO_ID_START + 1}",
        title_de=title, title_long_de=f"Demo-Geschäft: {title}",
        type_harmonized_de="Demo-Geschäft", state_name_harmonized_de="Eingereicht",
        begin_date=now, created_at=now, updated_at=now,
    )
    db.add(affair)
    db.flush()

    matches = AffairClassifier(db).accepted_title_matches(affair)
    if not matches:
        raise DemoNotificationError("The rule classifier did not assign a topic to the demo affair.")
    for match in matches:
        db.add(AffairClassification(
            affair_id=affair.id, category_id=match.category_id, score=match.score,
            confidence=confidence_for_match(match), classifier_version=CLASSIFIER_VERSION,
            classified_at=now,
        ))
    db.flush()

    event = create_change_event(
        db, affair_id=affair.id, dataset="affairs", source_id=affair.id, change_type="created",
        fingerprint=hashlib.sha256(f"demo:{affair.id}:{title}".encode()).hexdigest(),
        description="Demo affair created for a notification test.",
    )
    notifications = db.scalar(select(func.count()).select_from(Notification).where(
        Notification.change_event_id == event.id, Notification.user_id == user.id)) or 0

    names = db.scalars(select(ClassificationCategory.name_de).where(
        ClassificationCategory.id.in_([match.category_id for match in matches]))).all()
    hints = []
    if notifications == 0:
        hints.append("The demo affair does not match your saved subscription. Check topics, cantons, "
                     "keywords and the selected datasets, save them and try again.")
    return DemoResult(affair_id=affair.id, title=title, canton=body.canton_key, categories=sorted(names),
                      notifications_for_user=notifications, hints=hints)
