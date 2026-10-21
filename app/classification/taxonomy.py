"""Editable taxonomy. Stable codes preserve historical database references."""
import json
import os
from pathlib import Path

# Shorter infix terms would match inside unrelated words.
MIN_INFIX_LENGTH = 8


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
                if concept.get("match_type", "phrase") not in {"phrase", "prefix", "infix"} or concept.get("rule_type", "strong") not in {"strong", "context", "qualifier", "exclusion"}:
                    raise ValueError(f"Invalid matching rule: {code}")
                if concept.get("match_type") == "infix" and any(
                        len(term.strip()) < MIN_INFIX_LENGTH for terms in concept.get("terms", {}).values() for term in terms or []):
                    raise ValueError(f"Infix terms need at least {MIN_INFIX_LENGTH} characters: {code}/{concept['code']}")
                if not set(concept.get("scopes", ["title", "content"])) <= {"title", "content"} or not concept.get("scopes", ["title"]):
                    raise ValueError(f"Invalid scopes: {code}/{concept['code']}")
            for replaced in category.get("replaces", []):
                if not isinstance(replaced, str) or not replaced.strip():
                    raise ValueError(f"Invalid replaced category code: {code}")
    if global_fallbacks != 1:
        raise ValueError("Exactly one global fallback is required")
    return taxonomy


TAXONOMY = load_taxonomy()
