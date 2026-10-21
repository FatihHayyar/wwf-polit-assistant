"""Decide whether a change event concerns a user.

A *subject* is ``(entity, category_ids, canton, affair_types)``: the changed
record itself and, for linked records, the affairs it belongs to. A user is
notified if one of their record watches covers a subject or if at least one
active subscription profile matches it.
"""
from sqlalchemy import select

from app.models.change_event_affair import ChangeEventAffair
from app.models.entity_classification import EntityClassification
from app.models.classification import ClassificationCategory
from app.models.entities import Affair, Body, Meeting
from app.models.monitoring_subscription import UserRecordWatch
from app.models.subscription_profile import SubscriptionProfile
from app.services.entity_registry import ENTITIES


def ancestors(db, ids):
    result = set(ids)
    pending = set(result)
    while pending:
        parents = {value for value in db.scalars(select(ClassificationCategory.parent_id).where(
            ClassificationCategory.id.in_(pending))) if value is not None} - result
        result |= parents
        pending = parents
    return result


def affair_types(affair):
    return {affair.type_harmonized_de} if affair.type_harmonized_de else set()


def event_subjects(db, event):
    from app.services.notification_service import get_category_and_ancestor_ids
    ids = set(db.scalars(select(ChangeEventAffair.affair_id).where(ChangeEventAffair.change_event_id == event.id)))
    if event.affair_id is not None:
        ids.add(event.affair_id)
    subjects = []
    for affair_id in sorted(ids):
        affair = db.get(Affair, affair_id)
        if affair is not None:
            canton = db.scalar(select(Body.canton_key).where(Body.id == affair.body_id))
            subjects.append((affair, get_category_and_ancestor_ids(db, affair_id), canton, affair_types(affair)))
    if event.dataset != "affairs" and event.dataset in ENTITIES:
        entity = db.get(ENTITIES[event.dataset].model, event.source_id)
        if entity is not None:
            categories = ancestors(db, db.scalars(select(EntityClassification.category_id).where(
                EntityClassification.dataset == event.dataset, EntityClassification.entity_id == event.source_id)))
            canton = db.scalar(select(Body.canton_key).where(Body.id == entity.body_id))
            # A keyword in an agenda may match its affair's classification.
            # Keep inherited category/canton/type combinations together across
            # multi-affair meetings.
            inherited_subjects = list(subjects)
            for _, inherited_categories, inherited_canton, inherited_types in inherited_subjects:
                if canton is None or canton == inherited_canton:
                    subjects.append((entity, categories | inherited_categories, canton or inherited_canton, inherited_types))
            subjects.append((entity, categories, canton, set()))
    return subjects


def watched_entity(db, watches, subjects):
    """Explicit watches stay active when topic filters or classifications change."""
    for entity, *_ in subjects:
        for watch in watches:
            if type(entity) is ENTITIES[watch.dataset].model:
                key = entity.pk if watch.dataset == "documents" else entity.id
                if key == watch.record_id:
                    return entity
            if watch.dataset == "meetings" and getattr(entity, "meeting_id", None) == watch.record_id:
                return entity
            if watch.dataset == "groups":
                group_id = getattr(entity, "group_id", None)
                if group_id is None and getattr(entity, "meeting_id", None) is not None:
                    group_id = db.scalar(select(Meeting.group_id).where(Meeting.id == entity.meeting_id))
                if group_id == watch.record_id:
                    return entity
    return None


def dataset_allowed(db, datasets, dataset, subjects):
    """An empty selection means all datasets; affairs/meetings/groups include their linked records."""
    if not datasets or dataset in datasets:
        return True
    for entity, *_ in subjects:
        if "affairs" in datasets and isinstance(entity, Affair):
            return True
        if "meetings" in datasets and (isinstance(entity, Meeting) or getattr(entity, "meeting_id", None) is not None):
            return True
        if "groups" in datasets:
            group_id = getattr(entity, "group_id", None)
            if group_id is None and getattr(entity, "meeting_id", None) is not None:
                group_id = db.scalar(select(Meeting.group_id).where(Meeting.id == entity.meeting_id))
            if group_id is not None:
                return True
    return False


def profile_matches(db, profile, dataset, subjects):
    if not profile.active or not profile.has_filters:
        return None
    if not dataset_allowed(db, set(profile.datasets or []), dataset, subjects):
        return None
    categories = set(profile.category_ids or [])
    cantons = {key.strip().upper() for key in profile.canton_keys or []}
    keywords = set(profile.keywords or [])
    types = set(profile.affair_types or [])
    return next((entity for entity, ids, canton, entity_types in subjects
                 if (not categories or categories.intersection(ids))
                 and (not cantons or (canton and canton.strip().upper() in cantons))
                 and (not keywords or keyword_matches(entity, keywords))
                 and (not types or types.intersection(entity_types))), None)


def matching_subject(db, user_id, dataset, subjects):
    """Return the entity that makes the event relevant for the user, or None."""
    watches = db.scalars(select(UserRecordWatch).where(UserRecordWatch.user_id == user_id)).all()
    entity = watched_entity(db, watches, subjects)
    if entity is not None:
        return entity
    for profile in db.scalars(select(SubscriptionProfile).where(SubscriptionProfile.user_id == user_id)
                              .order_by(SubscriptionProfile.id)):
        entity = profile_matches(db, profile, dataset, subjects)
        if entity is not None:
            return entity
    return None


def matching_profiles(db, user_id, dataset, subjects):
    """Names of the user's profiles that match; used to explain notifications."""
    return [profile.name for profile in db.scalars(select(SubscriptionProfile).where(
        SubscriptionProfile.user_id == user_id).order_by(SubscriptionProfile.id))
        if profile_matches(db, profile, dataset, subjects) is not None]


def keyword_matches(entity, keywords):
    spec = next(spec for spec in ENTITIES.values() if type(entity) is spec.model)
    content = "\n".join(str(getattr(entity, field) or "") for field in spec.title_fields).casefold()
    return any(keyword.casefold() in content for keyword in keywords)
