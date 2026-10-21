"""Measure the rule classifier on the held-out sample of real affairs.

The sample was drawn at random and labelled blind (see the fixture header).
The script classifies the stored inputs in a temporary SQLite database, so
PostgreSQL is neither required nor modified. It also scores the production
classifications that were stored when the sample was drawn.

    python -m scripts.evaluate_holdout
"""
from __future__ import annotations

import gzip
import json
import math
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from app.classification.classifier import CLASSIFIER_VERSION, AffairClassifier
from app.classification.taxonomy import load_taxonomy
from app.db.database import Base
from scripts.seed_classification import seed_taxonomy

FIXTURE = Path("tests/fixtures/classification_holdout_2026-10-21.json.gz")
EVIDENCE_DIR = Path("docs/05-testing/evidence")
OTHER = "other"


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kwargs):
    return "INTEGER"


def load_fixture(path: Path = FIXTURE) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as source:
        return json.load(source)


def parent_map(taxonomy) -> dict[str, str]:
    """Map every category code to its main topic code."""
    mapping = {}
    for parent in taxonomy:
        mapping[parent["code"]] = parent["code"]
        for child in parent.get("children", []):
            mapping[child["code"]] = parent["code"]
    return mapping


def classify(records, taxonomy=None) -> dict[int, set[str]]:
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            seed_taxonomy(db, taxonomy or load_taxonomy())
            classifier = AffairClassifier(db)
            result = {}
            for record in records:
                affair = SimpleNamespace(id=record["id"], **record["input"]["affair"])
                texts = [SimpleNamespace(id=i, **text) for i, text in enumerate(record["input"]["texts"])]
                matches = classifier.accepted_matches(affair, texts)
                result[record["id"]] = {classifier.categories[m.category_id].code for m in matches} or {OTHER}
            return result
    finally:
        engine.dispose()


def is_ambiguous(expected) -> bool:
    return not expected["required"] and not expected.get("required_any")


def is_relevant(expected) -> bool:
    return bool(set(expected["required"]) - {OTHER} or expected.get("required_any"))


def score_record(expected, proposed: set[str]) -> dict:
    """Strict check: every required topic found and nothing outside the accepted set."""
    required = set(expected["required"])
    groups = [set(group) for group in expected.get("required_any", [])]
    allowed = required | set(expected.get("optional", [])) | set().union(*groups)
    missing = sorted(required - proposed)
    missing_any = [sorted(group) for group in groups if not proposed & group]
    extra = sorted(proposed - allowed)
    return {"correct": not missing and not missing_any and not extra,
            "missing": missing, "missing_any": missing_any, "extra": extra}


def ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 3) if denominator else None


def wilson_interval(successes: int, total: int, z: float = 1.96) -> list[float] | None:
    """95 % Wilson score interval; robust for small samples and extreme rates."""
    if not total:
        return None
    rate = successes / total
    centre = (rate + z * z / (2 * total)) / (1 + z * z / total)
    margin = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return [round(max(0.0, centre - margin), 3), round(min(1.0, centre + margin), 3)]


def binary_metrics(records, predictions) -> dict:
    """WWF relevance (any topic vs. other) on the non-ambiguous records."""
    counts = Counter()
    for record in records:
        expected = record["expected"]
        if is_ambiguous(expected):
            continue
        gold = is_relevant(expected)
        predicted = predictions[record["id"]] != {OTHER}
        counts[("tp" if gold else "fp") if predicted else ("fn" if gold else "tn")] += 1
    tp, fp, fn, tn = (counts[key] for key in ("tp", "fp", "fn", "tn"))
    precision, recall = ratio(tp, tp + fp), ratio(tp, tp + fn)
    f1 = round(2 * precision * recall / (precision + recall), 3) if precision and recall else None
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall, "f1": f1,
            "precision_ci95": wilson_interval(tp, tp + fp), "recall_ci95": wilson_interval(tp, tp + fn),
            "accuracy": ratio(tp + tn, tp + fp + fn + tn), "records": tp + fp + fn + tn}


def main_topic_metrics(records, predictions, parents) -> dict:
    """Micro-averaged main-topic precision and recall plus per-topic counts."""
    per_topic = {code: Counter() for code in set(parents.values()) if code != OTHER}
    micro = Counter()
    for record in records:
        expected = record["expected"]
        predicted = {parents[code] for code in predictions[record["id"]] if code != OTHER}
        required = {parents[code] for code in expected["required"] if code != OTHER}
        groups = [{parents[code] for code in group} for group in expected.get("required_any", [])]
        allowed = required | {parents[code] for code in expected.get("optional", []) if code != OTHER}
        allowed |= set().union(*groups)
        for topic in predicted:
            hit = topic in required or any(topic in group for group in groups)
            if hit:
                micro["tp"] += 1
                per_topic[topic]["tp"] += 1
            elif topic not in allowed:
                micro["fp"] += 1
                per_topic[topic]["fp"] += 1
        for topic in required - predicted:
            micro["fn"] += 1
            per_topic[topic]["fn"] += 1
        for group in groups:
            if not group & predicted and not group & required:
                micro["fn"] += 1
                if len(group) == 1:
                    per_topic[next(iter(group))]["fn"] += 1
    topics = {code: {"tp": c["tp"], "fp": c["fp"], "fn": c["fn"], "precision": ratio(c["tp"], c["tp"] + c["fp"]),
                     "recall": ratio(c["tp"], c["tp"] + c["fn"])} for code, c in sorted(per_topic.items())}
    return {"micro_precision": ratio(micro["tp"], micro["tp"] + micro["fp"]),
            "micro_recall": ratio(micro["tp"], micro["tp"] + micro["fn"]), "counts": dict(micro), "topics": topics}


def evaluate(fixture: dict, predictions: dict[int, set[str]], parents: dict[str, str]) -> dict:
    records = fixture["records"]
    scored = [{"id": r["id"], "title": r["title"], "proposed": sorted(predictions[r["id"]]),
               "ambiguous": is_ambiguous(r["expected"]), "relevant": is_relevant(r["expected"]),
               **score_record(r["expected"], predictions[r["id"]])} for r in records]
    ambiguous = [s for s in scored if s["ambiguous"]]
    return {
        "records": len(records),
        "strict_correct": sum(s["correct"] for s in scored),
        "ambiguous_records": len(ambiguous),
        "ambiguous_classified_as_topic": sum(s["proposed"] != [OTHER] for s in ambiguous),
        "relevance": binary_metrics(records, predictions),
        "main_topics": main_topic_metrics(records, predictions, parents),
        "errors": [s for s in scored if not s["correct"]],
    }


def topic_name(taxonomy, code) -> str:
    for parent in taxonomy:
        if parent["code"] == code:
            return parent["names"]["de"]
    return code


def report(fixture, current, production, taxonomy) -> str:
    relevance = current["relevance"]
    lines = [
        "# Klassifikation auf einem unabhängigen Prüfset",
        "",
        f"**Stand: {fixture['sampling']['date']}, Klassifikator `{CLASSIFIER_VERSION}`.** "
        "Erzeugt mit `python -m scripts.evaluate_holdout`.",
        "",
        "## Vorgehen",
        "",
        f"- **Stichprobe:** {current['records']} zufällige Geschäfte aus {fixture['sampling']['population_size']:,} "
        "Geschäften (reproduzierbare Zufallsreihenfolge über einen festen Seed), ohne die 50 Entwicklungsbeispiele."
        .replace(",", "'"),
        "- **Annotation:** blind vor Einsicht in die Klassifikatorausgaben, anhand der Kategoriendefinitionen der "
        "Taxonomie. Annotiert hat ein KI-Assistent, nicht WWF-Fachpersonen; die Labels sind deshalb eine "
        "nachvollziehbare Referenz, aber keine fachliche Abnahme.",
        "- **Mehrdeutige Datensätze** (z. B. allgemeine Raumplanung, öV-Angebot, Lärm) zählen in der "
        "Relevanzmessung nicht und gelten als korrekt, solange die Zuordnung vertretbar ist.",
        "- Die Stichprobe ist natürlich verteilt: Nur ein kleiner Teil der Geschäfte betrifft WWF-Themen. "
        "Die Zahl der positiven Fälle ist deshalb klein, und die Konfidenzintervalle sind entsprechend breit.",
        "",
        "## Ergebnisse",
        "",
        "| Kennzahl | Aktuelle Regeln | Produktion (gespeichert) |",
        "|---|---:|---:|",
    ]
    def with_ci(metrics, key):
        interval = metrics[f"{key}_ci95"]
        return f"{metrics[key]} ({interval[0]}–{interval[1]})" if interval else metrics[key]

    rows = [
        ("Datensätze streng korrekt", f"{current['strict_correct']}/{current['records']}", f"{production['strict_correct']}/{production['records']}"),
        ("WWF-Relevanz: Precision (95 %-KI)", with_ci(current["relevance"], "precision"), with_ci(production["relevance"], "precision")),
        ("WWF-Relevanz: Recall (95 %-KI)", with_ci(current["relevance"], "recall"), with_ci(production["relevance"], "recall")),
        ("WWF-Relevanz: F1", current["relevance"]["f1"], production["relevance"]["f1"]),
        ("WWF-Relevanz: Accuracy", current["relevance"]["accuracy"], production["relevance"]["accuracy"]),
        ("Hauptthemen: Precision (micro)", current["main_topics"]["micro_precision"], production["main_topics"]["micro_precision"]),
        ("Hauptthemen: Recall (micro)", current["main_topics"]["micro_recall"], production["main_topics"]["micro_recall"]),
    ]
    lines += [f"| {label} | {a} | {b} |" for label, a, b in rows]
    lines += [
        "",
        f"Relevanzmatrix (aktuelle Regeln, {relevance['records']} eindeutige Datensätze): "
        f"TP {relevance['tp']}, FP {relevance['fp']}, FN {relevance['fn']}, TN {relevance['tn']}. "
        f"Mehrdeutige Datensätze: {current['ambiguous_records']}, davon "
        f"{current['ambiguous_classified_as_topic']} einem WWF-Thema zugeordnet.",
        "",
        "| Hauptthema | TP | FP | FN | Precision | Recall |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for code, values in current["main_topics"]["topics"].items():
        lines.append(f"| {topic_name(taxonomy, code)} | {values['tp']} | {values['fp']} | {values['fn']} | "
                     f"{values['precision'] if values['precision'] is not None else '–'} | "
                     f"{values['recall'] if values['recall'] is not None else '–'} |")
    lines += ["", "## Abweichungen", "",
              "| Geschäft | Titel | Zuordnung | Fehlend | Zusätzlich |", "|---|---|---|---|---|"]
    for error in current["errors"]:
        title = error["title"].replace("|", "\\|")[:110]
        missing = ", ".join(error["missing"] + ["/".join(group) for group in error["missing_any"]]) or "–"
        lines.append(f"| {error['id']} | {title} | {', '.join(error['proposed'])} | {missing} | {', '.join(error['extra']) or '–'} |")
    lines += ["", "## Einordnung", "",
              "Das Entwicklungsset (50/50) misst nur, ob die Regeln die Beispiele erfüllen, an denen sie verbessert wurden. "
              "Dieses Prüfset schätzt die Qualität auf ungesehenen Daten. Es darf nicht zum Anpassen der Regeln verwendet "
              "werden; nach Regeländerungen wird erneut gemessen und für weitere Optimierungen ein neues Prüfset gezogen. "
              "Eine Bewertung durch WWF-Fachpersonen bleibt notwendig.", ""]
    return "\n".join(lines)


def run() -> dict:
    fixture = load_fixture()
    taxonomy = load_taxonomy()
    parents = parent_map(taxonomy)
    current = evaluate(fixture, classify(fixture["records"], taxonomy), parents)
    production = evaluate(fixture, {r["id"]: set(r["production_v7"]) or {OTHER} for r in fixture["records"]}, parents)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    result = {"version": CLASSIFIER_VERSION, "current_rules": current, "production_v7": production}
    (EVIDENCE_DIR / "holdout_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE_DIR / "holdout-evaluation.md").write_text(report(fixture, current, production, taxonomy), encoding="utf-8")
    summary = {key: current[key] for key in ("records", "strict_correct", "relevance")}
    summary["main_topics"] = {k: current["main_topics"][k] for k in ("micro_precision", "micro_recall")}
    print(json.dumps(summary, ensure_ascii=False))
    return result


if __name__ == "__main__":
    run()
