from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ClassificationCategory(Base):
    __tablename__ = "classification_categories"
    __table_args__ = (
        UniqueConstraint(
            "code",
            name="uq_classification_categories_code",
        ),
        Index(
            "idx_classification_categories_parent_id",
            "parent_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "classification_categories.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    name_de: Mapped[str] = mapped_column(Text, nullable=False)
    name_fr: Mapped[str] = mapped_column(Text, nullable=False)
    name_it: Mapped[str] = mapped_column(Text, nullable=False)
    name_rm: Mapped[str] = mapped_column(Text, nullable=False)

    description_de: Mapped[str | None] = mapped_column(Text)
    description_fr: Mapped[str | None] = mapped_column(Text)
    description_it: Mapped[str | None] = mapped_column(Text)
    description_rm: Mapped[str | None] = mapped_column(Text)

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_fallback: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    classification_threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=8.0,
    )


class ClassificationRule(Base):
    __tablename__ = "classification_rules"
    __table_args__ = (
        Index(
            "idx_classification_rules_category_id",
            "category_id",
        ),
        Index(
            "idx_classification_rules_active",
            "active",
        ),
        Index(
            "idx_classification_rules_language",
            "language",
        ),
        Index(
            "idx_classification_rules_concept_code",
            "concept_code",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "classification_categories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # Groups DE/FR/IT/RM synonyms into one semantic concept.
    # Example:
    # renewable_electricity_001
    #   DE: Photovoltaik
    #   FR: photovoltaïque
    #   IT: fotovoltaico
    #   RM: fotovoltaica
    concept_code: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )
    term: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    match_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    scope: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    rule_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    description: Mapped[str | None] = mapped_column(Text)


class AffairClassification(Base):
    __tablename__ = "affair_classifications"
    __table_args__ = (
        UniqueConstraint(
            "affair_id",
            "category_id",
            name="uq_affair_classifications_affair_category",
        ),
        Index(
            "idx_affair_classifications_affair_id",
            "affair_id",
        ),
        Index(
            "idx_affair_classifications_category_id",
            "category_id",
        ),
        Index(
            "idx_affair_classifications_confidence",
            "confidence",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    affair_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "classification_categories.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    confidence: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    classifier_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    classified_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )


class ClassificationEvidence(Base):
    __tablename__ = "classification_evidence"
    __table_args__ = (
        Index(
            "idx_classification_evidence_classification_id",
            "classification_id",
        ),
        Index(
            "idx_classification_evidence_rule_id",
            "rule_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    classification_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "affair_classifications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    rule_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "classification_rules.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    source_language: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )
    source_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    matched_term: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    excerpt: Mapped[str | None] = mapped_column(Text)