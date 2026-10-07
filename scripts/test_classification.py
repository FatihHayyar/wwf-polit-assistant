from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select

from app.classification.classifier import (
    AffairClassifier,
    confidence_for_match,
)
from app.db.database import SessionLocal
from app.models import (
    Affair,
    ClassificationCategory,
    ParliamentaryText,
)


BATCH_SIZE = 5000
TITLE_SAMPLE_LIMIT = 10
CONTENT_SAMPLE_LIMIT = 10


def affair_title(affair: Affair) -> str:
    return (
        affair.title_de
        or affair.title_fr
        or affair.title_it
        or affair.title_rm
        or "(no title)"
    )


def print_match(
    affair: Affair,
    match,
    categories: dict[int, ClassificationCategory],
) -> None:
    category = categories[match.category_id]

    source = (
        "TITLE"
        if match.title_strong > 0
        else "CONTENT"
    )

    print()
    print("=" * 100)
    print(f"Affair {affair.id}")
    print(f"Title: {affair_title(affair)}")
    print(
        f"  -> {category.name_de}"
        f" | score={match.score:.1f}"
        f" | confidence={confidence_for_match(match)}"
        f" | source={source}"
    )
    print(
        f"     title_strong={match.title_strong}, "
        f"content_strong={match.content_strong}"
    )
    print(
        f"     concepts={sorted(match.scored_concepts)}"
    )
    print(
        f"     terms={sorted(match.matched_terms)}"
    )


def main() -> None:
    db = SessionLocal()

    try:
        classifier = AffairClassifier(db)

        categories = {
            category.id: category
            for category in db.scalars(
                select(ClassificationCategory)
            ).all()
        }

        title_samples = 0
        content_samples = 0
        scanned = 0
        last_affair_id = 0

        while True:
            affairs = db.scalars(
                select(Affair)
                .where(Affair.id > last_affair_id)
                .order_by(Affair.id)
                .limit(BATCH_SIZE)
            ).all()

            if not affairs:
                break

            last_affair_id = affairs[-1].id
            scanned += len(affairs)

            unresolved: list[Affair] = []

            # Phase 1:
            # Title only. Strong title evidence is enough.
            for affair in affairs:
                matches = classifier.accepted_matches(
                    affair,
                    [],
                )

                title_matches = [
                    match
                    for match in matches
                    if match.title_strong > 0
                ]

                if title_matches:
                    if title_samples < TITLE_SAMPLE_LIMIT:
                        for match in title_matches:
                            if title_samples >= TITLE_SAMPLE_LIMIT:
                                break

                            print_match(
                                affair,
                                match,
                                categories,
                            )
                            title_samples += 1
                else:
                    unresolved.append(affair)

            # Phase 2:
            # Only affairs not classified from title need content.
            if (
                unresolved
                and content_samples < CONTENT_SAMPLE_LIMIT
            ):
                unresolved_ids = [
                    affair.id
                    for affair in unresolved
                ]

                text_rows = db.scalars(
                    select(ParliamentaryText).where(
                        ParliamentaryText.affair_id.in_(
                            unresolved_ids
                        )
                    )
                ).all()

                texts_by_affair: dict[
                    int,
                    list[ParliamentaryText],
                ] = defaultdict(list)

                for text_row in text_rows:
                    if text_row.affair_id is not None:
                        texts_by_affair[
                            text_row.affair_id
                        ].append(text_row)

                for affair in unresolved:
                    texts = texts_by_affair.get(
                        affair.id,
                        [],
                    )

                    if not texts:
                        continue

                    matches = classifier.accepted_matches(
                        affair,
                        texts,
                    )

                    content_matches = [
                        match
                        for match in matches
                        if (
                            match.title_strong == 0
                            and match.content_strong >= 2
                        )
                    ]

                    for match in content_matches:
                        if content_samples >= CONTENT_SAMPLE_LIMIT:
                            break

                        print_match(
                            affair,
                            match,
                            categories,
                        )
                        content_samples += 1

                    if content_samples >= CONTENT_SAMPLE_LIMIT:
                        break

            print(
                f"\rScanned: {scanned:,} affairs"
                f" | title: {title_samples}/{TITLE_SAMPLE_LIMIT}"
                f" | content: {content_samples}/{CONTENT_SAMPLE_LIMIT}",
                end="",
                flush=True,
            )

            if (
                title_samples >= TITLE_SAMPLE_LIMIT
                and content_samples >= CONTENT_SAMPLE_LIMIT
            ):
                break

        print()
        print()
        print("=" * 100)
        print(f"Scanned affairs: {scanned:,}")
        print(
            f"Title samples: "
            f"{title_samples}/{TITLE_SAMPLE_LIMIT}"
        )
        print(
            f"Content samples: "
            f"{content_samples}/{CONTENT_SAMPLE_LIMIT}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()