"""Editable taxonomy. Stable codes preserve historical database references."""
import json
import os
from pathlib import Path


def load_taxonomy(path=None):
    source = Path(path or os.getenv("CLASSIFICATION_TAXONOMY_PATH") or Path(__file__).with_name("taxonomy.json"))
    taxonomy = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(taxonomy, list) or not taxonomy:
        raise ValueError("Taxonomy must be a non-empty list")
    codes = set()
    global_fallbacks = 0
    for main in taxonomy:
        global_fallbacks += bool(main.get("fallback"))
        children = main.get("children", [])
        if not main.get("fallback") and sum(bool(c.get("fallback")) for c in children) != 1:
            raise ValueError("Each main category needs exactly one fallback child")
        for category in [main, *children]:
            code = category.get("code")
            if not isinstance(code, str) or not code.strip() or len(code)>100 or code in codes:
                raise ValueError(f"Invalid or duplicate category code: {code!r}")
            codes.add(code)
            names = category.get("names", {})
            if any(not isinstance(names.get(lang), str) or not names[lang].strip() for lang in ("de", "fr", "it", "rm")):
                raise ValueError(f"Missing category name: {code}")
            if float(category.get("threshold", 8)) <= 0:
                raise ValueError(f"Invalid threshold: {code}")
            concepts = set()
            for concept in category.get("concepts", []):
                if not concept.get("code") or concept["code"] in concepts:
                    raise ValueError(f"Invalid or duplicate concept: {code}")
                concepts.add(concept["code"])
                if concept.get("match_type", "phrase") not in {"phrase", "prefix"} or concept.get("rule_type", "strong") not in {"strong", "context", "qualifier"}:
                    raise ValueError(f"Invalid matching rule: {code}")
    if global_fallbacks != 1:
        raise ValueError("Exactly one global fallback is required")
    return taxonomy


TAXONOMY = load_taxonomy()
