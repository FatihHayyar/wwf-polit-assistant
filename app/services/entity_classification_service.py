from sqlalchemy import delete, select

from app.classification.classifier import AffairClassifier, CLASSIFIER_VERSION, confidence_for_match
from app.models.entity_classification import EntityClassification
from app.models.classification import ClassificationCategory
from app.models.entities import Affair, ParliamentaryText
from app.services.entity_relations import entity_key


def classify_entity(db, dataset, entity, classifier=None):
    classifier = classifier or AffairClassifier(db)
    values = {}
    for language in ("de", "fr", "it", "rm"):
        title = (getattr(entity, "title_" + language, None)
                 or getattr(entity, "name_" + language, None))
        if dataset == "agendas" and language == (entity.item_language or "de"):
            title = entity.item_title
        if dataset == "documents" and language == (entity.language or "de"):
            title = entity.name
        values["title_" + language] = title
    texts = [entity] if dataset == "texts" else []
    if dataset == "documents" and entity.text:
        language = entity.language if entity.language in {"de", "fr", "it", "rm"} else "de"
        texts = [ParliamentaryText(id=entity.pk, **{"text_" + language: entity.text})]
    matches = classifier.accepted_matches(Affair(id=entity_key(dataset, entity), **values), texts)
    db.execute(delete(EntityClassification).where(EntityClassification.dataset == dataset,
                                                  EntityClassification.entity_id == entity_key(dataset, entity)))
    for match in matches:
        db.add(EntityClassification(dataset=dataset, entity_id=entity_key(dataset, entity),
               category_id=match.category_id, score=match.score, confidence=confidence_for_match(match),
               classifier_version=CLASSIFIER_VERSION))
    if not matches:
        fallback = db.scalar(select(ClassificationCategory.id).where(
            ClassificationCategory.active.is_(True), ClassificationCategory.is_fallback.is_(True)))
        if fallback is None:
            raise RuntimeError("Seed the classification taxonomy before running sync")
        db.add(EntityClassification(dataset=dataset, entity_id=entity_key(dataset, entity), category_id=fallback,
               score=0, confidence="fallback", classifier_version=CLASSIFIER_VERSION))
    db.flush()
