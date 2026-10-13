from sqlalchemy import delete, select

from app.classification.classifier import AffairClassifier, CLASSIFIER_VERSION, confidence_for_match
from app.models.entity_classification import EntityClassification
from app.models.classification import ClassificationCategory
from app.models.entities import Affair, ParliamentaryText
from app.services.entity_relations import entity_key


def classification_input(dataset, entity):
    values = {}
    for language in ("de", "fr", "it", "rm"):
        title = (getattr(entity, "title_" + language, None)
                 or getattr(entity, "name_" + language, None))
        if dataset == "agendas" and language == (entity.item_language if entity.item_language in {"de", "fr", "it", "rm"} else "de"):
            title = entity.item_title
        if dataset == "documents" and language == (entity.language if entity.language in {"de", "fr", "it", "rm"} else "de"):
            title = entity.name
        values["title_" + language] = title
    texts = [entity] if dataset == "texts" else []
    if dataset == "documents" and entity.text:
        language = entity.language if entity.language in {"de", "fr", "it", "rm"} else "de"
        texts = [ParliamentaryText(id=entity.pk, **{"text_" + language: entity.text})]
    supplemental = {}
    for language in ("de", "fr", "it", "rm"):
        value = getattr(entity, "description_" + language, None)
        if value:
            supplemental["text_" + language] = value
    if dataset == "agendas" and entity.item_description:
        language = entity.item_language if entity.item_language in {"de", "fr", "it", "rm"} else "de"
        supplemental["text_" + language] = entity.item_description
    if dataset == "events" and entity.details_text:
        supplemental["text_de"] = entity.details_text
    if supplemental:
        texts.append(ParliamentaryText(id=entity_key(dataset, entity), **supplemental))
    return Affair(id=entity_key(dataset, entity), **values), texts


def classify_entity(db, dataset, entity, classifier=None):
    classifier = classifier or AffairClassifier(db)
    affair, texts = classification_input(dataset, entity)
    matches = classifier.accepted_matches(affair, texts)
    db.execute(delete(EntityClassification).where(EntityClassification.dataset == dataset,
                                                  EntityClassification.entity_id == entity_key(dataset, entity)))
    for match in matches:
        db.add(EntityClassification(dataset=dataset, entity_id=entity_key(dataset, entity),
               category_id=match.category_id, score=match.score, confidence=confidence_for_match(match),
               classifier_version=CLASSIFIER_VERSION))
    if not matches:
        fallback = db.scalar(select(ClassificationCategory.id).where(
            ClassificationCategory.active.is_(True), ClassificationCategory.parent_id.is_(None), ClassificationCategory.is_fallback.is_(True)))
        if fallback is None:
            raise RuntimeError("Seed the classification taxonomy before running sync")
        db.add(EntityClassification(dataset=dataset, entity_id=entity_key(dataset, entity), category_id=fallback,
               score=0, confidence="fallback", classifier_version=CLASSIFIER_VERSION))
    db.flush()
