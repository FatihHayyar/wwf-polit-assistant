"""Read-only comparison of sequential and parallel bulk classification."""
import json
import re
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from sqlalchemy import select, text
from app.db.database import SessionLocal
from app.classification.classifier import AffairClassifier, normalize_text
from app.services.entity_registry import ENTITIES
from scripts.reclassify_rules import initialize_worker, classify_payload, payload


def main():
    records = json.loads(Path("tests/fixtures/rule_quality_50.json").read_text(encoding="utf-8"))["records"]
    inputs = [({"id": r["id"], **r["input"]["affair"]},
               [{"id": i, **t} for i, t in enumerate(r["input"]["texts"])]) for r in records]
    with SessionLocal() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        model = ENTITIES["documents"].model
        inputs.extend(payload("documents", r) for r in db.scalars(select(model).where(model.pk > 360000).order_by(model.pk).limit(250)))
        classifier = AffairClassifier(db)
        for titles, texts in inputs:
            for item in [titles, *texts]:
                for value in item.values():
                    if isinstance(value, str):
                        assert " ".join(value.split()) == re.sub(r"\s+", " ", value).strip()
        grouped = {scope: dict(indexes) for scope, indexes in classifier.anchor_indexes.items()}
        for scope, indexes in classifier.anchor_indexes.items():
            for language, (exact, prefixes, order, _) in list(indexes.items()):
                anchors = {words[0] for rule in classifier.rules[scope][language]
                           if (words := re.findall(r"\w+", normalize_text(rule.term)))}
                alternatives = "|".join(re.escape(a) for a in sorted(anchors, key=len, reverse=True))
                pattern = re.compile(rf"(?<!\w)(?:{alternatives})\w*(?!\w)") if anchors else re.compile(r"(?!)")
                indexes[language] = (exact, prefixes, order, pattern)
        started = perf_counter()
        original = [classify_payload(data, classifier) for data in inputs]
        original_seconds = perf_counter() - started
        classifier.anchor_indexes = grouped
        started = perf_counter()
        sequential = [classify_payload(data, classifier) for data in inputs]
        grouped_seconds = perf_counter() - started
        assert original == sequential, "Grouped anchor results differ"
        with ProcessPoolExecutor(max_workers=4, initializer=initialize_worker) as pool:
            parallel = list(pool.map(classify_payload, inputs, chunksize=1))
        assert sequential == parallel, "Parallel results differ"
        print(json.dumps({"identical": len(inputs), "database_writes": 0, "workers": 4,
                          "original_seconds": original_seconds, "grouped_seconds": grouped_seconds}))


if __name__ == "__main__":
    main()
