"""Batched rule backfill. Preview by default; --apply requires passing quality checks."""
import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack
from types import SimpleNamespace
from time import perf_counter

from sqlalchemy import delete, insert, select, text, func

from app.classification.classifier import AffairClassifier, CLASSIFIER_VERSION, confidence_for_match, TITLE_FIELDS, TEXT_FIELDS
from app.db.database import SessionLocal, engine
from app.models.classification import AffairClassification, ClassificationEvidence
from app.models.entity_classification import EntityClassification
from app.services.entity_classification_service import classification_input
from app.services.entity_registry import ENTITIES
from scripts.classify_affairs import classify_batch, load_fallback_category, persist_batch
from scripts.rule_quality import run as quality_check
from scripts.seed_classification import seed_taxonomy
from scripts.sync.run_all import SYNC_LOCK_ID


def initialize_worker():
    global worker_classifier
    with SessionLocal() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        worker_classifier = AffairClassifier(db)
        db.expunge_all()


def payload(dataset, record):
    affair, texts = classification_input(dataset, record)
    return ({"id": affair.id, **{name: getattr(affair, name, None)
             for fields in TITLE_FIELDS.values() for name in fields}},
            [{"id": item.id, **{name: getattr(item, name, None) for name in TEXT_FIELDS.values()}}
             for item in texts])


def classify_payload(data, classifier=None):
    classifier = classifier or worker_classifier
    affair, texts = data
    return [(match.category_id, match.score, confidence_for_match(match)) for match in
            classifier.accepted_matches(SimpleNamespace(**affair), [SimpleNamespace(**item) for item in texts])]


def run(dataset, apply=False, force=False, limit=None, batch_size=1000, workers=1):
    model = ENTITIES[dataset].model
    key = model.pk if dataset == "documents" else model.id
    classification = AffairClassification if dataset == "affairs" else EntityClassification
    reference = classification.affair_id if dataset == "affairs" else classification.entity_id
    last_id, completed, started = -1, 0, perf_counter()
    with ExitStack() as stack:
        db = stack.enter_context(SessionLocal())
        pool = stack.enter_context(ProcessPoolExecutor(max_workers=workers, initializer=initialize_worker)) if workers > 1 else None
        if not apply:
            db.execute(text("SET TRANSACTION READ ONLY"))
        classifier = AffairClassifier(db)
        fallback = load_fallback_category(db)
        while limit is None or completed < limit:
            statement = select(model).where(key > last_id)
            if not force:
                exists = select(reference).where(reference == key)
                if dataset != "affairs":
                    exists = exists.where(classification.dataset == dataset)
                current = exists.where(classification.classifier_version == CLASSIFIER_VERSION)
                outdated = exists.where(classification.classifier_version != CLASSIFIER_VERSION)
                statement = statement.where(~current.exists() | outdated.exists())
            size = min(batch_size, limit - completed) if limit is not None else batch_size
            records = db.scalars(statement.order_by(key).limit(size)).all()
            if not records:
                break
            ids = [getattr(record, key.key) for record in records]
            if dataset == "affairs":
                rows, matches, _, _ = classify_batch(db, classifier=classifier, affairs=records, fallback_category=fallback)
                if apply:
                    old_ids = select(AffairClassification.id).where(AffairClassification.affair_id.in_(ids))
                    db.execute(delete(ClassificationEvidence).where(ClassificationEvidence.classification_id.in_(old_ids)))
                    db.execute(delete(AffairClassification).where(AffairClassification.affair_id.in_(ids)))
                    persist_batch(db, classification_rows=rows, accepted_matches=matches)
            else:
                rows = []
                inputs = [payload(dataset, record) for record in records]
                results = pool.map(classify_payload, inputs, chunksize=1) if pool else (classify_payload(data, classifier) for data in inputs)
                for id, matches in zip(ids, results):
                    if not matches:
                        rows.append(dict(dataset=dataset, entity_id=id, category_id=fallback.id,
                                         score=0, confidence="fallback", classifier_version=CLASSIFIER_VERSION))
                    else:
                        for category_id, score, confidence in matches:
                            rows.append(dict(dataset=dataset, entity_id=id, category_id=category_id,
                                             score=score, confidence=confidence,
                                             classifier_version=CLASSIFIER_VERSION))
                if apply:
                    db.execute(delete(EntityClassification).where(EntityClassification.dataset == dataset,
                                                                 EntityClassification.entity_id.in_(ids)))
                    db.execute(insert(EntityClassification), rows)
            if apply:
                db.commit()
            completed += len(records)
            last_id = ids[-1]
            print(json.dumps({"dataset": dataset, "apply": apply, "processed": completed,
                              "last_id": last_id, "rows": len(rows), "seconds": round(perf_counter() - started, 2)}), flush=True)
            db.expunge_all()
        if not apply:
            db.rollback()
        remaining = select(func.count()).select_from(model).where(~select(reference).where(
            reference == key, classification.classifier_version == CLASSIFIER_VERSION,
            *([classification.dataset == dataset] if dataset != "affairs" else [])).exists())
        result = {"dataset": dataset, "processed": completed, "remaining": db.scalar(remaining),
                  "seconds": round(perf_counter() - started, 2), "apply": apply}
        print(json.dumps({"completed": result}), flush=True)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=list(ENTITIES))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--force", action="store_true", help="Also rebuild current-version classifications after taxonomy edits")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1), help="Read-only classification workers for documents/texts")
    args = parser.parse_args()
    if args.batch_size < 1 or args.workers < 1 or (args.limit is not None and args.limit < 1):
        parser.error("Limits must be positive")
    if args.apply:
        result = quality_check()
        if result["correct"] != result["records"]:
            raise RuntimeError("Quality gate failed; database unchanged")
    with engine.connect() as lock:
        if not lock.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": SYNC_LOCK_ID}):
            raise RuntimeError("Synchronization is running; retry when it completes")
        lock.commit()
        try:
            if args.apply:
                with SessionLocal() as db:
                    print("Taxonomy:", seed_taxonomy(db), flush=True)
                    db.commit()
            for dataset in ([args.dataset] if args.dataset else ENTITIES):
                size = min(args.batch_size, 250) if dataset in {"documents", "texts"} else args.batch_size
                run(dataset, args.apply, args.force, args.limit, size,
                    args.workers if dataset in {"documents", "texts"} else 1)
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": SYNC_LOCK_ID})
            lock.commit()


if __name__ == "__main__":
    main()
