from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.classification.taxonomy import TAXONOMY
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
    category.classification_threshold = DEFAULT_THRESHOLD

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
    rule.match_type = "phrase"
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

    # category içindeki normalize edilmiş termlerin hangi
    # semantic concept'e ait olduğunu takip eder.
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

                # Örn. Grossverbraucher / Großverbraucher:
                # casefold() sonrasında aynı string olur.
                # Aynı concept içindeyse ikinci DB rule'una
                # ihtiyacımız yok; matcher zaten casefold eder.
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

                if rule_type == "context":
                    title_weight = (
                        TITLE_CONTEXT_WEIGHT
                    )
                    content_weight = (
                        CONTENT_CONTEXT_WEIGHT
                    )
                else:
                    title_weight = (
                        TITLE_STRONG_WEIGHT
                    )
                    content_weight = (
                        CONTENT_STRONG_WEIGHT
                    )

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
                    scope="title",
                    rule_type=rule_type,
                    weight=title_weight,
                )

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
                    scope="content",
                    rule_type=rule_type,
                    weight=content_weight,
                )

                count += 2

    return count

def seed() -> None:
    db = SessionLocal()

    try:
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
            TAXONOMY,
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
                        parent_id=parent.id,
                        sort_order=(
                            child_position * 10
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

        db.commit()

        active_rules = db.scalars(
            select(
                ClassificationRule
            ).where(
                ClassificationRule.active.is_(
                    True
                )
            )
        ).all()

        active_concepts = {
            rule.concept_code
            for rule in active_rules
        }

        print()
        print(
            "CLASSIFICATION TAXONOMY SEEDED"
        )
        print(
            f"Categories:       "
            f"{category_count}"
        )
        print(
            f"Configured rules: "
            f"{configured_rule_count}"
        )
        print(
            f"Active rules:     "
            f"{len(active_rules)}"
        )
        print(
            f"Active concepts:  "
            f"{len(active_concepts)}"
        )
        print(
            f"Deactivated:      "
            f"{deactivated_rule_count}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()