"""Measure the rule classifier on held-out samples of real affairs.

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

FIXTURE = Path("tests/fixtures/classification_holdout_a_2026-10-21.json.gz")
FIXTURES = {"A": FIXTURE, "B": Path("tests/fixtures/classification_holdout_b_2026-10-21.json.gz")}
# Codes that no longer exist in the taxonomy but occur in stored labels.
LEGACY_PARENTS = {"large_consumers_datacenters": "climate_energy"}
EVIDENCE_DIR = Path("docs/05-testing/evidence")
# Frozen result of the first v8 run on set B, before any change informed by B.
FIRST_MEASUREMENT = EVIDENCE_DIR / "holdout_v8_first_measurement.json"
OTHER = "other"


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kwargs):
    return "INTEGER"


def load_fixture(path: Path = FIXTURE) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as source:
        return json.load(source)


def parent_map(taxonomy) -> dict[str, str]:
    """Map every category code to its main topic code."""
    mapping = dict(LEGACY_PARENTS)
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


def score_record(expected, proposed: set[str], parents: dict[str, str] | None = None) -> dict:
    """Strict check: every required topic found and nothing outside the accepted set.

    A required local fallback ("<main>_other") is also satisfied by another
    accepted subcategory of the same main topic: by definition the classifier
    only assigns the fallback when no specific subcategory applies.
    """
    required = set(expected["required"])
    groups = [set(group) for group in expected.get("required_any", [])]
    allowed = required | set(expected.get("optional", [])) | set().union(*groups)
    if parents:
        required = {code for code in required if not (
            code.endswith("_other") and any(other in allowed and other != code and parents.get(other) == parents.get(code)
                                            for other in proposed))}
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
               **score_record(r["expected"], predictions[r["id"]], parents)} for r in records]
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


def with_ci(metrics, key):
    interval = metrics[f"{key}_ci95"]
    return f"{metrics[key]} ({interval[0]}–{interval[1]})" if interval else metrics[key]


def metric_rows(current, production):
    return [
        ("Datensätze streng korrekt", f"{current['strict_correct']}/{current['records']}",
         f"{production['strict_correct']}/{production['records']}"),
        ("WWF-Relevanz: Precision (95 %-KI)", with_ci(current["relevance"], "precision"), with_ci(production["relevance"], "precision")),
        ("WWF-Relevanz: Recall (95 %-KI)", with_ci(current["relevance"], "recall"), with_ci(production["relevance"], "recall")),
        ("WWF-Relevanz: F1", current["relevance"]["f1"], production["relevance"]["f1"]),
        ("WWF-Relevanz: Accuracy", current["relevance"]["accuracy"], production["relevance"]["accuracy"]),
        ("Hauptthemen: Precision (micro)", current["main_topics"]["micro_precision"], production["main_topics"]["micro_precision"]),
        ("Hauptthemen: Recall (micro)", current["main_topics"]["micro_recall"], production["main_topics"]["micro_recall"]),
    ]


def set_section(name, fixture, current, production, taxonomy, note) -> list[str]:
    relevance = current["relevance"]
    sampling = fixture["sampling"]
    lines = [
        f"## Prüfset {name}",
        "",
        f"{current['records']} zufällige Geschäfte, gezogen am {sampling['date']} ({sampling['method']}). {note}",
        "",
        f"| Kennzahl | Aktuelle Regeln (`{CLASSIFIER_VERSION}`) | Gespeichert beim Ziehen (`rule-based-v7`) |",
        "|---|---:|---:|",
    ]
    lines += [f"| {label} | {a} | {b} |" for label, a, b in metric_rows(current, production)]
    lines += [
        "",
        f"Relevanzmatrix der aktuellen Regeln ({relevance['records']} eindeutige Datensätze): "
        f"TP {relevance['tp']}, FP {relevance['fp']}, FN {relevance['fn']}, TN {relevance['tn']}. "
        f"Mehrdeutige Datensätze: {current['ambiguous_records']}, davon "
        f"{current['ambiguous_classified_as_topic']} einem WWF-Thema zugeordnet.",
        "",
        "| Hauptthema | TP | FP | FN | Precision | Recall |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for code, values in current["main_topics"]["topics"].items():
        precision = values["precision"] if values["precision"] is not None else "–"
        recall = values["recall"] if values["recall"] is not None else "–"
        lines.append(f"| {topic_name(taxonomy, code)} | {values['tp']} | {values['fp']} | {values['fn']} | {precision} | {recall} |")
    lines += ["", f"### Abweichungen der aktuellen Regeln in Prüfset {name}", "",
              "| Geschäft | Titel | Zuordnung | Fehlend | Zusätzlich |", "|---|---|---|---|---|"]
    for error in current["errors"]:
        title = error["title"].replace("|", "\\|")[:110]
        missing = ", ".join(error["missing"] + ["/".join(group) for group in error["missing_any"]]) or "–"
        extra = ", ".join(error["extra"]) or "–"
        lines.append(f"| {error['id']} | {title} | {', '.join(error['proposed'])} | {missing} | {extra} |")
    return lines + [""]


def report(results, taxonomy) -> str:
    lines = [
        "# Klassifikation auf unabhängigen Prüfsets",
        "",
        f"**Klassifikator `{CLASSIFIER_VERSION}`.** Erzeugt mit `python -m scripts.evaluate_holdout`.",
        "",
        "## Vorgehen",
        "",
        "- **Stichproben:** je 300 zufällige Geschäfte in reproduzierbarer Zufallsreihenfolge (fester Seed), ohne "
        "Überschneidung mit dem Entwicklungsset und untereinander.",
        "- **Annotation:** blind vor Einsicht in die Klassifikatorausgaben, anhand der Kategoriendefinitionen. "
        "Annotiert hat ein KI-Assistent, nicht WWF-Fachpersonen; die Labels sind eine nachvollziehbare Referenz, "
        "aber keine fachliche Abnahme.",
        "- **Mehrdeutige Datensätze** (z. B. allgemeine Raumplanung, öV-Angebot, Lärm) zählen in der Relevanzmessung "
        "nicht und gelten als korrekt, solange die Zuordnung vertretbar ist.",
        "- **Natürliche Verteilung:** Nur ein kleiner Teil der Geschäfte betrifft WWF-Themen; die Konfidenzintervalle "
        "(Wilson, 95 %) sind deshalb breit.",
        "- **Reihenfolge:** Prüfset A wurde am 21. Oktober gezogen und hat `rule-based-v7` gemessen. Seine Fehlerliste "
        "floss in die Entwicklung von `rule-based-v8` ein; für v8 ist A deshalb **nicht mehr unabhängig**. Prüfset B "
        "wurde vor jeder Messung von v8 gezogen und annotiert und ist die massgebliche Messung für v8.",
        "",
    ]
    b, a = results["B"], results["A"]
    lines += set_section("B (massgeblich für v8)", b["fixture"], b["current"], b["production"], taxonomy,
                         "Vor der Messung von v8 gezogen und annotiert.")
    if FIRST_MEASUREMENT.exists():
        first = json.loads(FIRST_MEASUREMENT.read_text(encoding="utf-8"))["B"]["relevance"]
        lines += ["### Erstmessung auf Prüfset B", "",
                  f"Die erste Messung von v8 auf B ist unverändert in `{FIRST_MEASUREMENT.name}` gespeichert: "
                  f"TP {first['tp']}, FP {first['fp']}, FN {first['fn']}, TN {first['tn']}, Precision "
                  f"{with_ci(first, 'precision')}, Recall {with_ci(first, 'recall')}, F1 {first['f1']}. Danach wurde eine Fehlerursache korrigiert, die "
                  "auch ausserhalb von B auftrat (öffentliche Akteure wurden aus Vorstosstexten gelesen und verdrängten "
                  "das Klima-Auffangthema). Die Werte oben enthalten diese Korrektur; da sie B gesehen hat, ist die "
                  "Erstmessung die unabhängige Schätzung.", ""]
    lines += set_section("A (für v8 nicht mehr unabhängig)", a["fixture"], a["current"], a["production"], taxonomy,
                         "Unabhängige Messung von v7; für v8 nur noch Entwicklungsdaten.")
    lines += ["## Einordnung", "",
              "Das Entwicklungsset (50/50) misst nur, ob die Regeln die Beispiele erfüllen, an denen sie verbessert wurden. "
              "Prüfsets schätzen die Qualität auf ungesehenen Daten. Sie dürfen nicht zum Anpassen der Regeln verwendet "
              "werden; nach Regeländerungen wird ein neues Prüfset gezogen. Eine Bewertung durch WWF-Fachpersonen bleibt "
              "notwendig.", ""]
    return "\n".join(lines)


def run() -> dict:
    taxonomy = load_taxonomy()
    parents = parent_map(taxonomy)
    results = {}
    for name, path in FIXTURES.items():
        fixture = load_fixture(path)
        current = evaluate(fixture, classify(fixture["records"], taxonomy), parents)
        stored = {r["id"]: set(r["production_v7"]) or {OTHER} for r in fixture["records"]}
        results[name] = {"fixture": fixture, "current": current, "production": evaluate(fixture, stored, parents)}
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"version": CLASSIFIER_VERSION}
    for name, value in results.items():
        payload[name] = {"current_rules": value["current"], "production_v7": value["production"]}
    (EVIDENCE_DIR / "holdout_results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE_DIR / "holdout-evaluation.md").write_text(report(results, taxonomy), encoding="utf-8")
    for name, value in results.items():
        current = value["current"]
        summary = {key: current[key] for key in ("records", "strict_correct", "relevance")}
        summary["main_topics"] = {k: current["main_topics"][k] for k in ("micro_precision", "micro_recall")}
        print(name, json.dumps(summary, ensure_ascii=False))
    return payload


if __name__ == "__main__":
    run()
