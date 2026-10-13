"""Verify rule backfill coverage without modifying PostgreSQL."""
import json
from pathlib import Path
from sqlalchemy import select, func, text
from app.db.database import SessionLocal
from app.classification.classifier import CLASSIFIER_VERSION
from app.models.classification import AffairClassification
from app.models.entity_classification import EntityClassification
from app.services.entity_registry import ENTITIES


def main():
    results = []
    with SessionLocal() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        for dataset, spec in ENTITIES.items():
            model = spec.model
            key = model.pk if dataset == "documents" else model.id
            classification = AffairClassification if dataset == "affairs" else EntityClassification
            reference = classification.affair_id if dataset == "affairs" else classification.entity_id
            conditions = [] if dataset == "affairs" else [classification.dataset == dataset]
            total = db.scalar(select(func.count()).select_from(model))
            covered = db.scalar(select(func.count()).select_from(model).where(select(reference).where(
                reference == key, classification.classifier_version == CLASSIFIER_VERSION, *conditions).exists()))
            outdated = db.scalar(select(func.count()).select_from(classification).join(model, reference == key).where(
                classification.classifier_version != CLASSIFIER_VERSION, *conditions))
            results.append(dict(dataset=dataset, total=total, covered=covered, missing=total-covered, outdated_rows=outdated))
    result = dict(version=CLASSIFIER_VERSION, total=sum(r["total"] for r in results),
                  complete=all(r["missing"] == 0 and r["outdated_rows"] == 0 for r in results), datasets=results)
    Path("rule_backfill_status.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
