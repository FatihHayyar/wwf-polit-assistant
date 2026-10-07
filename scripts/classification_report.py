from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models import (
    Affair,
    AffairClassification,
    ClassificationCategory,
    ClassificationEvidence,
)


SAMPLE_SIZE = 5


def print_header(title: str) -> None:
    print()
    print("=" * 90)
    print(title)
    print("=" * 90)


def short_text(
    value: str | None,
    limit: int = 130,
) -> str:
    if not value:
        return "-"

    value = " ".join(value.split())

    if len(value) <= limit:
        return value

    return value[: limit - 3] + "..."


def category_distribution(
    db: Session,
    fallback_id: int,
) -> None:
    print_header(
        "CATEGORY DISTRIBUTION"
    )

    rows = db.execute(
        select(
            ClassificationCategory.code,
            ClassificationCategory.name_de,
            ClassificationCategory.parent_id,
            func.count(
                AffairClassification.id
            ).label("count"),
        )
        .join(
            AffairClassification,
            AffairClassification.category_id
            == ClassificationCategory.id,
        )
        .where(
            ClassificationCategory.id
            != fallback_id
        )
        .group_by(
            ClassificationCategory.id,
            ClassificationCategory.code,
            ClassificationCategory.name_de,
            ClassificationCategory.parent_id,
        )
        .order_by(
            func.count(
                AffairClassification.id
            ).desc()
        )
    ).all()

    total_specific = sum(
        row.count
        for row in rows
    )

    print(
        f"Specific classification rows: "
        f"{total_specific:,}"
    )
    print()

    for row in rows:
        percent = (
            row.count
            / total_specific
            * 100
            if total_specific
            else 0
        )

        print(
            f"{row.count:>7,}  "
            f"{percent:>6.2f}%  "
            f"{row.code:<35} "
            f"{row.name_de}"
        )


def source_distribution(
    db: Session,
    fallback_id: int,
) -> None:
    print_header(
        "TITLE VS CONTENT"
    )

    rows = db.execute(
        select(
            AffairClassification.confidence,
            func.count(
                AffairClassification.id
            ),
        )
        .where(
            AffairClassification.category_id
            != fallback_id
        )
        .group_by(
            AffairClassification.confidence
        )
        .order_by(
            AffairClassification.confidence
        )
    ).all()

    for confidence, count in rows:
        print(
            f"{confidence:<12} "
            f"{count:>7,}"
        )

    print()
    print(
        "Evidence source distribution:"
    )

    evidence_rows = db.execute(
        select(
            ClassificationEvidence.source_type,
            func.count(
                ClassificationEvidence.id
            ),
        )
        .group_by(
            ClassificationEvidence.source_type
        )
        .order_by(
            func.count(
                ClassificationEvidence.id
            ).desc()
        )
    ).all()

    for source_type, count in evidence_rows:
        print(
            f"{source_type:<20} "
            f"{count:>7,}"
        )


def multilabel_report(
    db: Session,
    fallback_id: int,
) -> None:
    print_header(
        "MULTI-LABEL AFFAIRS"
    )

    grouped = (
        select(
            AffairClassification.affair_id,
            func.count(
                AffairClassification.id
            ).label("category_count"),
        )
        .where(
            AffairClassification.category_id
            != fallback_id
        )
        .group_by(
            AffairClassification.affair_id
        )
        .subquery()
    )

    rows = db.execute(
        select(
            grouped.c.category_count,
            func.count(),
        )
        .group_by(
            grouped.c.category_count
        )
        .order_by(
            grouped.c.category_count
        )
    ).all()

    for category_count, affairs in rows:
        print(
            f"{category_count} categories: "
            f"{affairs:,} affairs"
        )


def top_terms(
    db: Session,
) -> None:
    print_header(
        "TOP MATCHED TERMS"
    )

    rows = db.execute(
        select(
            ClassificationEvidence.matched_term,
            ClassificationEvidence.source_language,
            func.count(
                ClassificationEvidence.id
            ).label("count"),
        )
        .group_by(
            ClassificationEvidence.matched_term,
            ClassificationEvidence.source_language,
        )
        .order_by(
            func.count(
                ClassificationEvidence.id
            ).desc()
        )
        .limit(40)
    ).all()

    for term, language, count in rows:
        print(
            f"{count:>6,}  "
            f"{language:<3}  "
            f"{term}"
        )


def category_samples(
    db: Session,
    fallback_id: int,
) -> None:
    print_header(
        "CATEGORY SAMPLES"
    )

    categories = db.scalars(
        select(
            ClassificationCategory
        )
        .where(
            ClassificationCategory.active.is_(True),
            ClassificationCategory.parent_id.is_not(
                None
            ),
            ClassificationCategory.id
            != fallback_id,
        )
        .order_by(
            ClassificationCategory.code
        )
    ).all()

    for category in categories:
        count = (
            db.scalar(
                select(
                    func.count(
                        AffairClassification.id
                    )
                ).where(
                    AffairClassification.category_id
                    == category.id
                )
            )
            or 0
        )

        if count == 0:
            continue

        print()
        print(
            f"[{category.code}] "
            f"{category.name_de} "
            f"({count:,})"
        )
        print("-" * 90)

        rows = db.execute(
            select(
                Affair.id,
                Affair.title_de,
                Affair.title_fr,
                Affair.title_it,
                AffairClassification.score,
                AffairClassification.confidence,
            )
            .join(
                AffairClassification,
                AffairClassification.affair_id
                == Affair.id,
            )
            .where(
                AffairClassification.category_id
                == category.id
            )
            .order_by(
                Affair.id
            )
            .limit(
                SAMPLE_SIZE
            )
        ).all()

        for row in rows:
            title = (
                row.title_de
                or row.title_fr
                or row.title_it
                or "-"
            )

            print(
                f"  Affair {row.id} "
                f"| score={row.score:.1f} "
                f"| {row.confidence}"
            )
            print(
                f"    {short_text(title)}"
            )


def suspicious_samples(
    db: Session,
    fallback_id: int,
) -> None:
    print_header(
        "CONTENT-ONLY SAMPLE FOR MANUAL REVIEW"
    )

    rows = db.execute(
        select(
            Affair.id,
            Affair.title_de,
            Affair.title_fr,
            Affair.title_it,
            ClassificationCategory.code,
            ClassificationCategory.name_de,
            AffairClassification.score,
        )
        .join(
            AffairClassification,
            AffairClassification.affair_id
            == Affair.id,
        )
        .join(
            ClassificationCategory,
            ClassificationCategory.id
            == AffairClassification.category_id,
        )
        .where(
            AffairClassification.category_id
            != fallback_id,
            AffairClassification.confidence
            == "medium",
        )
        .order_by(
            Affair.id
        )
        .limit(50)
    ).all()

    for row in rows:
        title = (
            row.title_de
            or row.title_fr
            or row.title_it
            or "-"
        )

        print(
            f"Affair {row.id} "
            f"| {row.code} "
            f"| score={row.score:.1f}"
        )
        print(
            f"  {short_text(title)}"
        )


def integrity_checks(
    db: Session,
    fallback_id: int,
) -> None:
    print_header(
        "INTEGRITY CHECKS"
    )

    total_affairs = (
        db.scalar(
            select(
                func.count(
                    Affair.id
                )
            )
        )
        or 0
    )

    classified_affairs = (
        db.scalar(
            select(
                func.count(
                    func.distinct(
                        AffairClassification.affair_id
                    )
                )
            )
        )
        or 0
    )

    fallback_with_specific = (
        db.scalar(
            select(
                func.count()
            ).select_from(
                AffairClassification
            ).where(
                AffairClassification.category_id
                == fallback_id,
                AffairClassification.affair_id.in_(
                    select(
                        AffairClassification.affair_id
                    ).where(
                        AffairClassification.category_id
                        != fallback_id
                    )
                ),
            )
        )
        or 0
    )

    orphan_classifications = (
        db.scalar(
            select(
                func.count(
                    AffairClassification.id
                )
            )
            .outerjoin(
                Affair,
                Affair.id
                == AffairClassification.affair_id,
            )
            .where(
                Affair.id.is_(None)
            )
        )
        or 0
    )

    print(
        f"Affairs:                         "
        f"{total_affairs:,}"
    )
    print(
        f"Distinct classified affairs:     "
        f"{classified_affairs:,}"
    )
    print(
        f"Missing classifications:         "
        f"{total_affairs - classified_affairs:,}"
    )
    print(
        f"Fallback + specific conflicts:   "
        f"{fallback_with_specific:,}"
    )
    print(
        f"Orphan classification rows:      "
        f"{orphan_classifications:,}"
    )

    if (
        total_affairs
        == classified_affairs
        and fallback_with_specific == 0
        and orphan_classifications == 0
    ):
        print()
        print(
            "INTEGRITY PASSED"
        )
    else:
        print()
        print(
            "INTEGRITY WARNING"
        )


def main() -> None:
    db = SessionLocal()

    try:
        fallback = db.scalar(
            select(
                ClassificationCategory
            ).where(
                ClassificationCategory.active.is_(True),
                ClassificationCategory.is_fallback.is_(True),
            )
        )

        if fallback is None:
            raise RuntimeError(
                "Fallback category not found."
            )

        print()
        print("=" * 90)
        print(
            "WWF POLIT ASSISTANT — "
            "CLASSIFICATION QUALITY REPORT"
        )
        print("=" * 90)

        integrity_checks(
            db,
            fallback.id,
        )

        category_distribution(
            db,
            fallback.id,
        )

        source_distribution(
            db,
            fallback.id,
        )

        multilabel_report(
            db,
            fallback.id,
        )

        top_terms(
            db
        )

        category_samples(
            db,
            fallback.id,
        )

        suspicious_samples(
            db,
            fallback.id,
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()