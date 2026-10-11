"""Backfill related entity classifications without creating notifications."""
import argparse
from sqlalchemy import select

from app.classification.classifier import AffairClassifier, CLASSIFIER_VERSION
from app.db.database import SessionLocal
from app.models.entity_classification import EntityClassification
from app.services.entity_classification_service import classify_entity
from app.services.entity_registry import ENTITIES


def run(dataset, force=False):
    model = ENTITIES[dataset].model
    key = model.pk if dataset == "documents" else model.id
    last_id = 0
    while True:
        with SessionLocal() as db:
            statement = select(model).where(key > last_id)
            if not force:
                statement = statement.where(~select(EntityClassification.entity_id).where(
                    EntityClassification.dataset == dataset, EntityClassification.entity_id == key,
                    EntityClassification.classifier_version == CLASSIFIER_VERSION).exists())
            rows = db.scalars(statement.order_by(key).limit(500)).all()
            if not rows:
                return
            classifier = AffairClassifier(db)
            for row in rows:
                classify_entity(db, dataset, row, classifier=classifier)
            db.commit()
            last_id = getattr(rows[-1], key.key)
            print(f"{dataset}: classified {len(rows)} records through {last_id}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=[key for key in ENTITIES if key != "affairs"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    for dataset in ([args.dataset] if args.dataset else [key for key in ENTITIES if key != "affairs"]):
        run(dataset, args.force)
