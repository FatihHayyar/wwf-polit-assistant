"""Compare the baseline rules with the configured rules on the 50-record development set.

The rules were tuned against these records, so the result is a regression check and
not an unbiased quality estimate. Use ``scripts.evaluate_holdout`` for the held-out set.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from app.classification.classifier import AffairClassifier, CLASSIFIER_VERSION
from app.classification.taxonomy import load_taxonomy
from app.db.database import Base
from scripts.seed_classification import seed_taxonomy

BASELINE_REVISION = "b20f074557c310f0b1a52df15ca3336de73ed56d"
EVIDENCE_DIR = Path("docs/05-testing/evidence")


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kwargs):
    return "INTEGER"


def score(expected, proposed):
    required = set(expected["required"])
    allowed = required | set(expected.get("optional", []))
    missing = sorted(required - proposed)
    missing_any = [g for g in expected.get("required_any", []) if not proposed.intersection(g)]
    extra = sorted(proposed - allowed)
    return {"correct": not missing and not missing_any and not extra,
            "missing": missing, "missing_any": missing_any, "extra": extra}


def evaluate(taxonomy, classifier_type, records):
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            seed_taxonomy(db, taxonomy)
            classifier = classifier_type(db)
            result = []
            for record in records:
                affair = SimpleNamespace(id=record["id"], **record["input"]["affair"])
                texts = [SimpleNamespace(id=i, **t) for i, t in enumerate(record["input"]["texts"])]
                matches = classifier.accepted_matches(affair, texts)
                codes = {classifier.categories[m.category_id].code for m in matches} or {"other"}
                result.append({"dataset": record["dataset"], "id": record["id"], "title": record["title"],
                               "group": record["group"], "proposed": sorted(codes),
                               **score(record["expected"], codes)})
            return result
    finally:
        engine.dispose()


def run():
    records = json.loads(Path("tests/fixtures/rule_quality_50.json").read_text(encoding="utf-8"))["records"]
    source = subprocess.check_output(["git", "show", f"{BASELINE_REVISION}:app/classification/taxonomy.py"], text=True, encoding="utf-8")
    assignment = next(n for n in ast.parse(source).body if isinstance(n, ast.Assign))
    baseline_taxonomy = ast.literal_eval(assignment.value)
    module = ModuleType("_baseline_rule_classifier")
    sys.modules[module.__name__] = module
    source = subprocess.check_output(["git", "show", f"{BASELINE_REVISION}:app/classification/classifier.py"], text=True, encoding="utf-8")
    exec(compile(source, "pushed_classifier.py", "exec"), module.__dict__)
    old = evaluate(baseline_taxonomy, module.AffairClassifier, records)
    new = evaluate(load_taxonomy(), AffairClassifier, records)
    summary = {"baseline_correct": sum(r["correct"] for r in old), "correct": sum(r["correct"] for r in new),
               "records": len(new), "database_writes": 0, "version": CLASSIFIER_VERSION,
               "groups": {group: {"total": sum(r["group"] == group for r in new),
                                   "correct": sum(r["correct"] for r in new if r["group"] == group)}
                          for group in {r["group"] for r in new}}}
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "rule_quality_results.json").write_text(json.dumps({"summary": summary, "baseline": old, "results": new},
                                                                      ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Regelqualität auf dem Entwicklungsset", "",
             f"Frühere Regeln: {summary['baseline_correct']}/50; aktuelle Regeln: {summary['correct']}/50. "
             "Beide Versionen wurden mit denselben 50 Quelldatensätzen in getrennten temporären SQLite-Datenbanken geprüft; "
             "PostgreSQL wurde nicht verändert.", "",
             "**Einschränkung:** Die Regeln wurden anhand dieser Beispiele verbessert. Das Ergebnis ist eine Regressionsprüfung "
             "und keine unverzerrte Qualitätsschätzung. Die Messung auf ungesehenen Daten steht in "
             "[holdout-evaluation.md](holdout-evaluation.md).", "",
             "| Quelle | Titel | Erwartete Pflichtcodes | Aktuelle Zuordnung | Ergebnis |", "|---|---|---|---|---|"]
    for source, result in zip(records, new):
        expected = ", ".join(source["expected"]["required"])
        if source["expected"].get("required_any"):
            expected += "; zusätzlich ein passendes Biodiversitätsthema"
        title = str(result["title"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {result['dataset']}:{result['id']} | {title} | {expected} | {', '.join(result['proposed'])} | "
                     + ("korrekt" if result["correct"] else "falsch") + " |")
    (EVIDENCE_DIR / "rule-quality-development-set.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    for r in new:
        if not r["correct"]:
            print(json.dumps(r, ensure_ascii=True))
    return summary


if __name__ == "__main__":
    run()
