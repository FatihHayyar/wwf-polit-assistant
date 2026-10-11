from sqlalchemy import select

from app.models.change_event_affair import ChangeEventAffair
from app.models.dataset_subscription import UserDatasetSubscription
from app.models.entity_classification import EntityClassification
from app.models.classification import ClassificationCategory
from app.models.entities import Affair, Body, Meeting
from app.models.monitoring_subscription import UserKeywordSubscription, UserRecordWatch
from app.models.subscription import UserCantonSubscription, UserCategorySubscription
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
            subjects.append((affair, get_category_and_ancestor_ids(db, affair_id), canton))
    if event.dataset != "affairs" and event.dataset in ENTITIES:
        entity = db.get(ENTITIES[event.dataset].model, event.source_id)
        if entity is not None:
            categories = ancestors(db, db.scalars(select(EntityClassification.category_id).where(
                EntityClassification.dataset == event.dataset, EntityClassification.entity_id == event.source_id)))
            canton = db.scalar(select(Body.canton_key).where(Body.id == entity.body_id))
            # A keyword in an agenda may match its affair's classification.
            # Keep inherited category/canton pairs together across multi-affair meetings.
            inherited_subjects = list(subjects)
            for _, inherited_categories, inherited_canton in inherited_subjects:
                if canton is None or canton == inherited_canton:
                    subjects.append((entity, categories | inherited_categories, canton or inherited_canton))
            subjects.append((entity, categories, canton))
    return subjects


def matching_subject(db, user_id, dataset, subjects):
    # Explicit watches remain active when topic filters or classifications change.
    watches = db.scalars(select(UserRecordWatch).where(UserRecordWatch.user_id == user_id)).all()
    for entity, _, _ in subjects:
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
    datasets = set(db.scalars(select(UserDatasetSubscription.dataset).where(UserDatasetSubscription.user_id == user_id)))
    if datasets and dataset not in datasets:
        contextual_match = False
        for entity, _, _ in subjects:
            if "affairs" in datasets and isinstance(entity, Affair):
                contextual_match = True
            if "meetings" in datasets and (isinstance(entity, Meeting) or getattr(entity,"meeting_id",None) is not None):
                contextual_match = True
            if "groups" in datasets:
                group_id = getattr(entity,"group_id",None)
                if group_id is None and getattr(entity,"meeting_id",None) is not None:
                    group_id = db.scalar(select(Meeting.group_id).where(Meeting.id == entity.meeting_id))
                if group_id is not None:
                    contextual_match = True
        if not contextual_match:
            return None
    categories = set(db.scalars(select(UserCategorySubscription.category_id).where(UserCategorySubscription.user_id == user_id)))
    cantons = set(db.scalars(select(UserCantonSubscription.canton_key).where(UserCantonSubscription.user_id == user_id)))
    keywords = set(db.scalars(select(UserKeywordSubscription.keyword).where(UserKeywordSubscription.user_id == user_id)))
    if not categories and not cantons and not keywords:
        return None
    return next((entity for entity, ids, canton in subjects
                 if (not categories or categories.intersection(ids))
                 and (not cantons or (canton and canton.strip().upper() in cantons))
                 and (not keywords or keyword_matches(entity, keywords))), None)


def keyword_matches(entity, keywords):
    spec = next(spec for spec in ENTITIES.values() if type(entity) is spec.model)
    content = "\n".join(str(getattr(entity, field) or "") for field in spec.title_fields).casefold()
    return any(keyword.casefold() in content for keyword in keywords)
