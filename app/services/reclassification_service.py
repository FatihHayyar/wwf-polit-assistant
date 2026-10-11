"""Replace classifications and evidence in the caller's transaction."""
from sqlalchemy import delete

from app.classification.classifier import AffairClassifier
from app.models.classification import AffairClassification, ClassificationEvidence
from app.models.entities import Affair


def reclassify_affairs(db, affair_ids: set[int]) -> None:
    if not affair_ids:
        return
    from scripts.classify_affairs import classify_batch, load_fallback_category, persist_batch

    db.flush()
    classifier = AffairClassifier(db)
    fallback = load_fallback_category(db)
    for affair_id in sorted(affair_ids):
        affair = db.get(Affair, affair_id)
        if affair is None:
            continue
        classification_ids = select_classification_ids(affair_id)
        db.execute(delete(ClassificationEvidence).where(
            ClassificationEvidence.classification_id.in_(classification_ids)
        ))
        db.execute(delete(AffairClassification).where(AffairClassification.affair_id == affair_id))
        rows, matches, _, _ = classify_batch(
            db, classifier=classifier, affairs=[affair], fallback_category=fallback,
        )
        persist_batch(db, classification_rows=rows, accepted_matches=matches)
    db.flush()


def select_classification_ids(affair_id):
    from sqlalchemy import select
    return select(AffairClassification.id).where(AffairClassification.affair_id == affair_id)
