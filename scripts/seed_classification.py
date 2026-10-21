from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.classification.taxonomy import load_taxonomy
from app.db.database import SessionLocal
from app.models import (
    ClassificationCategory,
    ClassificationRule,
)


TITLE_STRONG_WEIGHT = 10.0
TITLE_CONTEXT_WEIGHT = 2.0
CONTENT_STRONG_WEIGHT = 4.0
CONTENT_CONTEXT_WEIGHT = 1.0

DEFAULT_THRESHOLD = 8.0

SUPPORTED_LANGUAGES = (
    "de",
    "fr",
    "it",
    "rm",
)

RuleKey = tuple[
    int,
    str,
    str,
    str,
    str,
]


def normalize_term(term: str) -> str:
    return term.casefold().strip()


def get_or_create_category(
    db: Session,
    *,
    code: str,
    names: dict[str, str],
    parent_id: int | None,
    sort_order: int,
    is_fallback: bool = False,
    threshold: float = DEFAULT_THRESHOLD,
    descriptions: dict | None = None,
) -> ClassificationCategory:
    category = db.scalar(
        select(ClassificationCategory).where(
            ClassificationCategory.code == code
        )
    )

    if category is None:
        category = ClassificationCategory(
            code=code,
        )
        db.add(category)

    category.parent_id = parent_id
    category.name_de = names["de"]
    category.name_fr = names["fr"]
    category.name_it = names["it"]
    category.name_rm = names["rm"]
    category.sort_order = sort_order
    category.active = True
    category.is_fallback = is_fallback
    category.classification_threshold = threshold
    for language in SUPPORTED_LANGUAGES:
        setattr(category, "description_" + language, (descriptions or {}).get(language))

    db.flush()

    return category


def make_rule_key(
    *,
    category_id: int,
    concept_code: str,
    language: str,
    term: str,
    scope: str,
) -> RuleKey:
    return (
        category_id,
        concept_code,
        language,
        normalize_term(term),
        scope,
    )


def load_existing_rules(
    db: Session,
) -> dict[RuleKey, ClassificationRule]:
    rules = db.scalars(
        select(ClassificationRule)
    ).all()

    result: dict[
        RuleKey,
        ClassificationRule,
    ] = {}

    for rule in rules:
        key = make_rule_key(
            category_id=rule.category_id,
            concept_code=rule.concept_code,
            language=rule.language,
            term=rule.term,
            scope=rule.scope,
        )

        if key in result:
            raise RuntimeError(
                "Duplicate classification rule identity "
                f"found in database: {key}"
            )

        result[key] = rule

    return result


def upsert_rule(
    db: Session,
    *,
    existing_rules: dict[
        RuleKey,
        ClassificationRule,
    ],
    configured_rule_ids: set[int],
    category_id: int,
    concept_code: str,
    language: str,
    term: str,
    scope: str,
    rule_type: str,
    weight: float,
    match_type: str = "phrase",
) -> ClassificationRule:
    key = make_rule_key(
        category_id=category_id,
        concept_code=concept_code,
        language=language,
        term=term,
        scope=scope,
    )

    rule = existing_rules.get(key)

    if rule is None:
        rule = ClassificationRule(
            category_id=category_id,
            concept_code=concept_code,
            language=language,
            term=term,
            scope=scope,
        )

        db.add(rule)

        existing_rules[key] = rule

    rule.concept_code = concept_code
    rule.language = language
    rule.term = term
    rule.match_type = match_type
    rule.scope = scope
    rule.rule_type = rule_type
    rule.weight = weight
    rule.active = True
    rule.description = (
        f"{rule_type} {scope} evidence"
    )

    db.flush()

    configured_rule_ids.add(rule.id)

    return rule


def add_category_rules(
    db: Session,
    *,
    category: ClassificationCategory,
    category_code: str,
    concepts: list[dict],
    existing_rules: dict[
        RuleKey,
        ClassificationRule,
    ],
    configured_rule_ids: set[int],
) -> int:
    count = 0

    seen_concept_codes: set[str] = set()

    # Tracks which semantic concept each normalized term
    # of the category belongs to.
    seen_category_terms: dict[
        tuple[str, str],
        str,
    ] = {}

    for concept in concepts:
        local_concept_code = (
            concept["code"].strip()
        )

        if not local_concept_code:
            raise ValueError(
                "Empty concept code in category "
                f"{category_code}"
            )

        if local_concept_code in seen_concept_codes:
            raise ValueError(
                "Duplicate concept code in category "
                f"{category_code}: "
                f"{local_concept_code}"
            )

        seen_concept_codes.add(
            local_concept_code
        )

        concept_code = (
            f"{category_code}_"
            f"{local_concept_code}"
        )

        rule_type = concept.get(
            "rule_type",
            "strong",
        )

        if rule_type not in {
            "strong",
            "context",
            "qualifier",
            "exclusion",
        }:
            raise ValueError(
                f"Invalid rule_type "
                f"{rule_type!r} for "
                f"{concept_code}"
            )

        terms = concept.get(
            "terms",
            {},
        )

        for language in SUPPORTED_LANGUAGES:
            language_terms = terms.get(
                language,
                [],
            )

            seen_terms: set[str] = set()

            for raw_term in language_terms:
                term = raw_term.strip()

                if not term:
                    continue

                normalized = normalize_term(
                    term
                )

                # E.g. Grossverbraucher / Großverbraucher:
                # terms become identical after casefold(). Within the
                # same concept no second DB rule is needed because
                # the matcher casefolds as well.
                if normalized in seen_terms:
                    continue

                seen_terms.add(
                    normalized
                )

                category_term_key = (
                    language,
                    normalized,
                )

                previous_concept = (
                    seen_category_terms.get(
                        category_term_key
                    )
                )

                if (
                    previous_concept is not None
                    and previous_concept
                    != concept_code
                ):
                    raise ValueError(
                        "Same normalized term assigned "
                        "to different concepts in "
                        f"{category_code}/{language}: "
                        f"{term!r} -> "
                        f"{previous_concept} and "
                        f"{concept_code}"
                    )

                seen_category_terms[
                    category_term_key
                ] = concept_code

                if rule_type == "exclusion":
                    # Exclusions suppress their category and add no score.
                    title_weight = content_weight = 0.0
                elif rule_type == "context":
                    title_weight = (
                        TITLE_CONTEXT_WEIGHT
                    )
                    content_weight = (
                        CONTENT_CONTEXT_WEIGHT
                    )
                elif rule_type == "qualifier":
                    title_weight = TITLE_STRONG_WEIGHT
                    content_weight = DEFAULT_THRESHOLD - CONTENT_CONTEXT_WEIGHT
                else:
                    title_weight = (
                        TITLE_STRONG_WEIGHT
                    )
                    content_weight = (
                        CONTENT_STRONG_WEIGHT
                    )

                # Very common words (e.g. "Kanton") carry signal in a title
                # but not in long texts; such concepts are limited to titles.
                for scope in concept.get("scopes", ["title", "content"]):
                    upsert_rule(
                        db,
                        existing_rules=existing_rules,
                        configured_rule_ids=(
                            configured_rule_ids
                        ),
                        category_id=category.id,
                        concept_code=concept_code,
                        language=language,
                        term=term,
                        scope=scope,
                        rule_type=rule_type,
                        match_type=concept.get("match_type", "phrase"),
                        weight=title_weight if scope == "title" else content_weight,
                    )
                    count += 1

    return count

def seed_taxonomy(db: Session, taxonomy=None):
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    existing_rules = (
        load_existing_rules(db)
    )

    configured_rule_ids: set[int] = set()
    configured_category_codes: set[str] = set()

    category_count = 0
    configured_rule_count = 0

    for (
        main_position,
        main,
    ) in enumerate(
        taxonomy,
        start=1,
    ):
        main_code = main["code"]

        configured_category_codes.add(
            main_code
        )

        parent = get_or_create_category(
            db,
            code=main_code,
            names=main["names"],
            threshold=main.get("threshold", DEFAULT_THRESHOLD),
            descriptions=main.get("descriptions"),
            parent_id=None,
            sort_order=main.get(
                "sort_order",
                main_position * 10,
            ),
            is_fallback=main.get(
                "fallback",
                False,
            ),
        )

        category_count += 1

        for (
            child_position,
            child,
        ) in enumerate(
            main.get(
                "children",
                [],
            ),
            start=1,
        ):
            child_code = child["code"]

            configured_category_codes.add(
                child_code
            )

            category = (
                get_or_create_category(
                    db,
                    code=child_code,
                    names=child["names"],
                    threshold=child.get("threshold", DEFAULT_THRESHOLD),
                    descriptions=child.get("descriptions"),
                    parent_id=parent.id,
                    sort_order=(
                        child.get("sort_order", child_position * 10)
                    ),
                    is_fallback=child.get(
                        "fallback",
                        False,
                    ),
                )
            )

            category_count += 1

            configured_rule_count += (
                add_category_rules(
                    db,
                    category=category,
                    category_code=child_code,
                    concepts=child.get(
                        "concepts",
                        [],
                    ),
                    existing_rules=(
                        existing_rules
                    ),
                    configured_rule_ids=(
                        configured_rule_ids
                    ),
                )
            )

    categories = db.scalars(
        select(
            ClassificationCategory
        )
    ).all()

    for category in categories:
        category.active = (
            category.code
            in configured_category_codes
        )

    all_rules = db.scalars(
        select(
            ClassificationRule
        )
    ).all()

    deactivated_rule_count = 0

    for rule in all_rules:
        if (
            rule.id
            not in configured_rule_ids
        ):
            if rule.active:
                deactivated_rule_count += 1

            rule.active = False

    moved_subscriptions = transfer_replaced_subscriptions(db, taxonomy)

    return {"categories": category_count, "rules": configured_rule_count,
            "deactivated_rules": deactivated_rule_count,
            "transferred_subscriptions": moved_subscriptions}


def transfer_replaced_subscriptions(db: Session, taxonomy) -> int:
    """Give subscribers of a split or renamed category its successors.

    A category may declare ``"replaces": ["old_code"]``. Profiles subscribed
    to the old category keep receiving the same topics after the change.
    """
    from app.models.subscription_profile import SubscriptionProfile

    by_code = {category.code: category for category in db.scalars(select(ClassificationCategory))}
    successors = {}
    for main in taxonomy:
        for category in [main, *main.get("children", [])]:
            for old_code in category.get("replaces", []):
                old = by_code.get(old_code)
                if old is not None and old.code != category["code"]:
                    successors.setdefault(old.id, set()).add(by_code[category["code"]].id)
    transferred = 0
    if not successors:
        return transferred
    for profile in db.scalars(select(SubscriptionProfile)):
        selected = set(profile.category_ids or [])
        added = set().union(*(successors[old] for old in selected if old in successors)) - selected
        if added:
            profile.category_ids = sorted(selected | added)
            transferred += 1
    db.flush()
    return transferred

def seed():
    with SessionLocal() as db:
        result = seed_taxonomy(db)
        db.commit()
        print("Classification taxonomy synchronized:", result)


if __name__ == "__main__":
    seed()
