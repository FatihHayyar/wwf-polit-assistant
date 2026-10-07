from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from time import perf_counter

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.classification.classifier import (
    CLASSIFIER_VERSION,
    AffairClassifier,
    CategoryMatch,
    confidence_for_match,
)
from app.db.database import SessionLocal
from app.models import (
    Affair,
    AffairClassification,
    ClassificationCategory,
    ClassificationEvidence,
    ParliamentaryText,
)


BATCH_SIZE = 5000


def utc_now_naive() -> datetime:
    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


def load_fallback_category(
    db: Session,
) -> ClassificationCategory:
    category = db.scalar(
        select(
            ClassificationCategory
        ).where(
            ClassificationCategory.active.is_(
                True
            ),
            ClassificationCategory.is_fallback.is_(
                True
            ),
        )
    )

    if category is None:
        raise RuntimeError(
            "No active fallback category found."
        )

    return category


def find_resume_id(
    db: Session,
) -> int:
    """
    Find the largest continuous Affair ID range that has
    already been classified.

    We do NOT simply use MAX(classified affair_id), because
    that could skip holes after an interrupted run.
    """
    last_complete_id = 0

    rows = db.execute(
        select(
            Affair.id,
            AffairClassification.affair_id,
        )
        .outerjoin(
            AffairClassification,
            AffairClassification.affair_id
            == Affair.id,
        )
        .order_by(
            Affair.id
        )
    )

    current_affair_id = None
    current_has_classification = False

    for (
        affair_id,
        classified_affair_id,
    ) in rows:
        if (
            current_affair_id is None
        ):
            current_affair_id = affair_id
            current_has_classification = (
                classified_affair_id
                is not None
            )
            continue

        if affair_id != current_affair_id:
            if not current_has_classification:
                return last_complete_id

            last_complete_id = (
                current_affair_id
            )

            current_affair_id = affair_id
            current_has_classification = (
                classified_affair_id
                is not None
            )
        else:
            if classified_affair_id is not None:
                current_has_classification = True

    if current_affair_id is not None:
        if current_has_classification:
            last_complete_id = (
                current_affair_id
            )

    return last_complete_id


def count_processed_affairs(
    db: Session,
) -> int:
    return (
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


def load_affairs_batch(
    db: Session,
    *,
    last_affair_id: int,
) -> list[Affair]:
    return list(
        db.scalars(
            select(
                Affair
            )
            .where(
                Affair.id > last_affair_id
            )
            .order_by(
                Affair.id
            )
            .limit(
                BATCH_SIZE
            )
        ).all()
    )


def load_texts_for_affairs(
    db: Session,
    *,
    affair_ids: list[int],
) -> dict[
    int,
    list[ParliamentaryText],
]:
    if not affair_ids:
        return {}

    rows = db.scalars(
        select(
            ParliamentaryText
        ).where(
            ParliamentaryText.affair_id.in_(
                affair_ids
            )
        )
    ).all()

    result: dict[
        int,
        list[ParliamentaryText],
    ] = defaultdict(list)

    for row in rows:
        if row.affair_id is not None:
            result[
                row.affair_id
            ].append(
                row
            )

    return result


def classify_batch(
    db: Session,
    *,
    classifier: AffairClassifier,
    affairs: list[Affair],
    fallback_category: ClassificationCategory,
) -> tuple[
    list[dict],
    dict[
        tuple[int, int],
        CategoryMatch,
    ],
    Counter,
    int,
]:
    classification_rows: list[
        dict
    ] = []

    accepted_matches: dict[
        tuple[int, int],
        CategoryMatch,
    ] = {}

    stats = Counter()

    unresolved: list[
        Affair
    ] = []

    classified_at = (
        utc_now_naive()
    )

    # ---------------------------------------------
    # TITLE — exactly once per Affair
    # ---------------------------------------------

    for affair in affairs:
        matches = (
            classifier.accepted_title_matches(
                affair
            )
        )

        if not matches:
            unresolved.append(
                affair
            )
            continue

        stats["title_affairs"] += 1

        for match in matches:
            key = (
                affair.id,
                match.category_id,
            )

            accepted_matches[
                key
            ] = match

            classification_rows.append(
                {
                    "affair_id": affair.id,
                    "category_id": (
                        match.category_id
                    ),
                    "score": match.score,
                    "confidence": (
                        confidence_for_match(
                            match
                        )
                    ),
                    "classifier_version": (
                        CLASSIFIER_VERSION
                    ),
                    "classified_at": (
                        classified_at
                    ),
                }
            )

    # ---------------------------------------------
    # CONTENT — only unresolved Affairs
    # ---------------------------------------------

    unresolved_ids = [
        affair.id
        for affair in unresolved
    ]

    texts_by_affair = (
        load_texts_for_affairs(
            db,
            affair_ids=unresolved_ids,
        )
    )

    text_record_count = sum(
        len(items)
        for items
        in texts_by_affair.values()
    )

    for affair in unresolved:
        texts = texts_by_affair.get(
            affair.id,
            [],
        )

        matches = (
            classifier.accepted_content_matches(
                texts
            )
        )

        if not matches:
            classification_rows.append(
                {
                    "affair_id": affair.id,
                    "category_id": (
                        fallback_category.id
                    ),
                    "score": 0.0,
                    "confidence": "fallback",
                    "classifier_version": (
                        CLASSIFIER_VERSION
                    ),
                    "classified_at": (
                        classified_at
                    ),
                }
            )

            stats[
                "fallback_affairs"
            ] += 1

            continue

        stats[
            "content_affairs"
        ] += 1

        for match in matches:
            key = (
                affair.id,
                match.category_id,
            )

            accepted_matches[
                key
            ] = match

            classification_rows.append(
                {
                    "affair_id": affair.id,
                    "category_id": (
                        match.category_id
                    ),
                    "score": match.score,
                    "confidence": (
                        confidence_for_match(
                            match
                        )
                    ),
                    "classifier_version": (
                        CLASSIFIER_VERSION
                    ),
                    "classified_at": (
                        classified_at
                    ),
                }
            )

    return (
        classification_rows,
        accepted_matches,
        stats,
        text_record_count,
    )


def persist_batch(
    db: Session,
    *,
    classification_rows: list[
        dict
    ],
    accepted_matches: dict[
        tuple[int, int],
        CategoryMatch,
    ],
) -> tuple[int, int]:
    if not classification_rows:
        return 0, 0

    statement = (
        insert(
            AffairClassification
        )
        .values(
            classification_rows
        )
        .on_conflict_do_update(
            index_elements=[
                "affair_id",
                "category_id",
            ],
            set_={
                "score": (
                    insert(
                        AffairClassification
                    ).excluded.score
                ),
                "confidence": (
                    insert(
                        AffairClassification
                    ).excluded.confidence
                ),
                "classifier_version": (
                    insert(
                        AffairClassification
                    ).excluded.classifier_version
                ),
                "classified_at": (
                    insert(
                        AffairClassification
                    ).excluded.classified_at
                ),
            },
        )
        .returning(
            AffairClassification.id,
            AffairClassification.affair_id,
            AffairClassification.category_id,
        )
    )

    inserted = db.execute(
        statement
    ).all()

    classification_ids = {
        (
            row.affair_id,
            row.category_id,
        ): row.id
        for row in inserted
    }

    evidence_rows: list[
        dict
    ] = []

    for (
        key,
        match,
    ) in accepted_matches.items():
        classification_id = (
            classification_ids.get(
                key
            )
        )

        if classification_id is None:
            raise RuntimeError(
                "Missing classification ID "
                f"for {key}"
            )

        for evidence in (
            match.evidence
        ):
            evidence_rows.append(
                {
                    "classification_id": (
                        classification_id
                    ),
                    "rule_id": (
                        evidence.rule_id
                    ),
                    "source_type": (
                        evidence.source_type
                    ),
                    "source_language": (
                        evidence.language
                    ),
                    "source_id": (
                        evidence.source_id
                    ),
                    "matched_term": (
                        evidence.term
                    ),
                    "weight": (
                        evidence.weight
                    ),
                    "excerpt": None,
                }
            )

    if evidence_rows:
        db.execute(
            insert(
                ClassificationEvidence
            ),
            evidence_rows,
        )

    return (
        len(inserted),
        len(evidence_rows),
    )


def validate_results(
    db: Session,
) -> None:
    affair_count = (
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

    classification_count = (
        db.scalar(
            select(
                func.count(
                    AffairClassification.id
                )
            )
        )
        or 0
    )

    evidence_count = (
        db.scalar(
            select(
                func.count(
                    ClassificationEvidence.id
                )
            )
        )
        or 0
    )

    fallback_category = db.scalar(
        select(
            ClassificationCategory
        ).where(
            ClassificationCategory.active.is_(
                True
            ),
            ClassificationCategory.is_fallback.is_(
                True
            ),
        )
    )

    if fallback_category is None:
        raise RuntimeError(
            "Fallback category missing."
        )

    fallback_count = (
        db.scalar(
            select(
                func.count(
                    AffairClassification.id
                )
            ).where(
                AffairClassification.category_id
                == fallback_category.id
            )
        )
        or 0
    )

    missing = (
        affair_count
        - classified_affairs
    )

    print()
    print("=" * 72)
    print(
        "FINAL CLASSIFICATION VALIDATION"
    )
    print("=" * 72)
    print(
        f"Affairs:                  "
        f"{affair_count:,}"
    )
    print(
        f"Classified affairs:       "
        f"{classified_affairs:,}"
    )
    print(
        f"Classification rows:      "
        f"{classification_count:,}"
    )
    print(
        f"Evidence rows:            "
        f"{evidence_count:,}"
    )
    print(
        f"Fallback classifications: "
        f"{fallback_count:,}"
    )
    print(
        f"Missing affairs:          "
        f"{missing:,}"
    )

    if missing != 0:
        raise RuntimeError(
            f"{missing:,} affairs are "
            "not classified."
        )

    print()
    print(
        "VALIDATION PASSED"
    )


def main() -> None:
    db = SessionLocal()

    try:
        classifier = (
            AffairClassifier(
                db
            )
        )

        fallback_category = (
            load_fallback_category(
                db
            )
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

        existing_processed = (
            count_processed_affairs(
                db
            )
        )

        resume_id = find_resume_id(
            db
        )

        print()
        print("=" * 72)
        print(
            "RESUMABLE AFFAIR CLASSIFICATION"
        )
        print("=" * 72)
        print(
            f"Classifier:        "
            f"{CLASSIFIER_VERSION}"
        )
        print(
            f"Total affairs:     "
            f"{total_affairs:,}"
        )
        print(
            f"Already classified:"
            f" {existing_processed:,}"
        )
        print(
            f"Resume after ID:   "
            f"{resume_id:,}"
        )
        print(
            f"Batch size:        "
            f"{BATCH_SIZE:,}"
        )
        print()

        processed_this_run = 0

        while True:
            batch_started = (
                perf_counter()
            )

            affairs = (
                load_affairs_batch(
                    db,
                    last_affair_id=(
                        resume_id
                    ),
                )
            )

            if not affairs:
                break

            first_id = affairs[0].id
            last_id = affairs[-1].id

            classify_started = (
                perf_counter()
            )

            (
                classification_rows,
                accepted_matches,
                stats,
                text_record_count,
            ) = classify_batch(
                db,
                classifier=classifier,
                affairs=affairs,
                fallback_category=(
                    fallback_category
                ),
            )

            classify_seconds = (
                perf_counter()
                - classify_started
            )

            persist_started = (
                perf_counter()
            )

            (
                classification_count,
                evidence_count,
            ) = persist_batch(
                db,
                classification_rows=(
                    classification_rows
                ),
                accepted_matches=(
                    accepted_matches
                ),
            )

            db.commit()

            persist_seconds = (
                perf_counter()
                - persist_started
            )

            batch_seconds = (
                perf_counter()
                - batch_started
            )

            processed_this_run += len(
                affairs
            )

            resume_id = last_id

            total_done = (
                existing_processed
                + processed_this_run
            )

            percent = (
                total_done
                / total_affairs
                * 100
            )

            print(
                f"[{total_done:,}/{total_affairs:,}] "
                f"{percent:6.2f}% "
                f"| ids={first_id}-{last_id} "
                f"| texts={text_record_count:,} "
                f"| title={stats['title_affairs']:,} "
                f"| content={stats['content_affairs']:,} "
                f"| fallback={stats['fallback_affairs']:,} "
                f"| rows={classification_count:,} "
                f"| evidence={evidence_count:,} "
                f"| classify={classify_seconds:.1f}s "
                f"| db={persist_seconds:.1f}s "
                f"| total={batch_seconds:.1f}s"
            )

        validate_results(
            db
        )

        print()
        print("=" * 72)
        print(
            "CLASSIFICATION COMPLETE"
        )
        print("=" * 72)

    except KeyboardInterrupt:
        db.rollback()

        print()
        print(
            "Stopped by user. "
            "Completed batches remain committed."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()