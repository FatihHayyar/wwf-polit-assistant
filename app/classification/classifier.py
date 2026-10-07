from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Affair,
    ClassificationCategory,
    ClassificationRule,
    ParliamentaryText,
)


CLASSIFIER_VERSION = "rule-based-v6"

SUPPORTED_LANGUAGES = ("de", "fr", "it", "rm")

TITLE_FIELDS = {
    "de": ("title_de", "title_long_de"),
    "fr": ("title_fr", "title_long_fr"),
    "it": ("title_it", "title_long_it"),
    "rm": ("title_rm", "title_long_rm"),
}

TEXT_FIELDS = {
    "de": "text_de",
    "fr": "text_fr",
    "it": "text_it",
    "rm": "text_rm",
}


@dataclass(frozen=True)
class CompiledRule:
    id: int
    category_id: int
    concept_code: str
    language: str
    term: str
    scope: str
    rule_type: str
    weight: float
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class Evidence:
    rule_id: int
    concept_code: str
    term: str
    language: str
    scope: str
    rule_type: str
    weight: float
    source_type: str
    source_id: int | None


@dataclass
class CategoryMatch:
    category_id: int
    score: float = 0.0

    title_strong_concepts: set[str] = field(
        default_factory=set
    )
    title_context_concepts: set[str] = field(
        default_factory=set
    )
    content_strong_concepts: set[str] = field(
        default_factory=set
    )
    content_context_concepts: set[str] = field(
        default_factory=set
    )

    scored_concepts: set[str] = field(
        default_factory=set
    )

    matched_terms: set[str] = field(
        default_factory=set
    )

    evidence: list[Evidence] = field(
        default_factory=list
    )

    evidence_keys: set[
        tuple[int, str, int | None]
    ] = field(
        default_factory=set
    )

    @property
    def title_strong(self) -> int:
        return len(
            self.title_strong_concepts
        )

    @property
    def content_strong(self) -> int:
        return len(
            self.content_strong_concepts
        )


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize(
        "NFKC",
        value,
    ).casefold()

    value = re.sub(
        r"[\u2010\u2011\u2012\u2013\u2014\u2212]",
        "-",
        value,
    )

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def build_phrase_pattern(
    term: str,
) -> re.Pattern[str]:
    return re.compile(
        rf"(?<!\w){re.escape(term)}(?!\w)",
        re.IGNORECASE,
    )


def confidence_for_match(
    match: CategoryMatch,
) -> str:
    if match.title_strong >= 1:
        return "high"

    if match.content_strong >= 3:
        return "high"

    if match.content_strong >= 2:
        return "medium"

    return "low"


class AffairClassifier:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

        self.categories = {
            category.id: category
            for category in db.scalars(
                select(
                    ClassificationCategory
                ).where(
                    ClassificationCategory.active.is_(
                        True
                    )
                )
            )
        }

        self.rules = {
            scope: {
                language: []
                for language in SUPPORTED_LANGUAGES
            }
            for scope in (
                "title",
                "content",
            )
        }

        rules = db.scalars(
            select(
                ClassificationRule
            ).where(
                ClassificationRule.active.is_(
                    True
                )
            )
        ).all()

        for rule in rules:
            if rule.scope not in self.rules:
                continue

            if (
                rule.language
                not in SUPPORTED_LANGUAGES
            ):
                continue

            term = normalize_text(
                rule.term
            )

            if not term:
                continue

            self.rules[
                rule.scope
            ][
                rule.language
            ].append(
                CompiledRule(
                    id=rule.id,
                    category_id=rule.category_id,
                    concept_code=rule.concept_code,
                    language=rule.language,
                    term=rule.term,
                    scope=rule.scope,
                    rule_type=rule.rule_type,
                    weight=rule.weight,
                    pattern=build_phrase_pattern(
                        term
                    ),
                )
            )

    def _add_evidence(
        self,
        matches: dict[int, CategoryMatch],
        *,
        rule: CompiledRule,
        source_type: str,
        source_id: int | None,
    ) -> None:
        match = matches.setdefault(
            rule.category_id,
            CategoryMatch(
                category_id=rule.category_id
            ),
        )

        match.matched_terms.add(
            rule.term
        )

        effective_weight = 0.0

        if (
            rule.concept_code
            not in match.scored_concepts
        ):
            match.scored_concepts.add(
                rule.concept_code
            )

            effective_weight = rule.weight

            match.score += effective_weight

            if rule.scope == "title":
                if rule.rule_type == "strong":
                    match.title_strong_concepts.add(
                        rule.concept_code
                    )
                else:
                    match.title_context_concepts.add(
                        rule.concept_code
                    )
            else:
                if rule.rule_type == "strong":
                    match.content_strong_concepts.add(
                        rule.concept_code
                    )
                else:
                    match.content_context_concepts.add(
                        rule.concept_code
                    )

        evidence_key = (
            rule.id,
            source_type,
            source_id,
        )

        if evidence_key in match.evidence_keys:
            return

        match.evidence_keys.add(
            evidence_key
        )

        if effective_weight <= 0:
            return

        match.evidence.append(
            Evidence(
                rule_id=rule.id,
                concept_code=rule.concept_code,
                term=rule.term,
                language=rule.language,
                scope=rule.scope,
                rule_type=rule.rule_type,
                weight=effective_weight,
                source_type=source_type,
                source_id=source_id,
            )
        )

    def _match_text(
        self,
        matches: dict[int, CategoryMatch],
        *,
        value: str | None,
        language: str,
        scope: str,
        source_type: str,
        source_id: int | None,
    ) -> None:
        text = normalize_text(
            value
        )

        if not text:
            return

        for rule in self.rules[
            scope
        ][
            language
        ]:
            if rule.pattern.search(text):
                self._add_evidence(
                    matches,
                    rule=rule,
                    source_type=source_type,
                    source_id=source_id,
                )

    def classify_title(
        self,
        affair: Affair,
    ) -> list[CategoryMatch]:
        matches: dict[
            int,
            CategoryMatch,
        ] = {}

        for (
            language,
            fields,
        ) in TITLE_FIELDS.items():
            for field_name in fields:
                self._match_text(
                    matches,
                    value=getattr(
                        affair,
                        field_name,
                    ),
                    language=language,
                    scope="title",
                    source_type=field_name,
                    source_id=affair.id,
                )

        return list(
            matches.values()
        )

    def classify_content(
        self,
        texts: list[
            ParliamentaryText
        ],
    ) -> list[CategoryMatch]:
        matches: dict[
            int,
            CategoryMatch,
        ] = {}

        for text_record in texts:
            for (
                language,
                field_name,
            ) in TEXT_FIELDS.items():
                self._match_text(
                    matches,
                    value=getattr(
                        text_record,
                        field_name,
                    ),
                    language=language,
                    scope="content",
                    source_type="text",
                    source_id=text_record.id,
                )

        return list(
            matches.values()
        )

    def accepted_title_matches(
        self,
        affair: Affair,
    ) -> list[CategoryMatch]:
        accepted = [
            match
            for match in self.classify_title(
                affair
            )
            if match.title_strong >= 1
        ]

        accepted.sort(
            key=lambda item: (
                item.score,
                item.title_strong,
            ),
            reverse=True,
        )

        return accepted

    def accepted_content_matches(
        self,
        texts: list[
            ParliamentaryText
        ],
    ) -> list[CategoryMatch]:
        accepted: list[
            CategoryMatch
        ] = []

        for match in self.classify_content(
            texts
        ):
            category = self.categories.get(
                match.category_id
            )

            if category is None:
                continue

            if match.content_strong < 2:
                continue

            if (
                match.score
                < category.classification_threshold
            ):
                continue

            accepted.append(
                match
            )

        accepted.sort(
            key=lambda item: (
                item.score,
                item.content_strong,
            ),
            reverse=True,
        )

        return accepted

    def classify(
        self,
        affair: Affair,
        texts: list[
            ParliamentaryText
        ],
    ) -> list[CategoryMatch]:
        """
        Compatibility method for tests and callers that need
        the complete raw match set.
        """
        matches: dict[
            int,
            CategoryMatch,
        ] = {}

        for match in self.classify_title(
            affair
        ):
            matches[
                match.category_id
            ] = match

        for content_match in self.classify_content(
            texts
        ):
            existing = matches.get(
                content_match.category_id
            )

            if existing is None:
                matches[
                    content_match.category_id
                ] = content_match
                continue

            for concept in (
                content_match.content_strong_concepts
            ):
                existing.content_strong_concepts.add(
                    concept
                )

            for concept in (
                content_match.content_context_concepts
            ):
                existing.content_context_concepts.add(
                    concept
                )

            for term in (
                content_match.matched_terms
            ):
                existing.matched_terms.add(
                    term
                )

            for evidence in (
                content_match.evidence
            ):
                if (
                    evidence.concept_code
                    in existing.scored_concepts
                ):
                    continue

                existing.scored_concepts.add(
                    evidence.concept_code
                )
                existing.score += (
                    evidence.weight
                )
                existing.evidence.append(
                    evidence
                )

        return list(
            matches.values()
        )

    def accepted_matches(
        self,
        affair: Affair,
        texts: list[
            ParliamentaryText
        ],
    ) -> list[CategoryMatch]:
        title_matches = (
            self.accepted_title_matches(
                affair
            )
        )

        if title_matches:
            return title_matches

        return self.accepted_content_matches(
            texts
        )