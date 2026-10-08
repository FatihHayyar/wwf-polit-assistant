from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from app.classification.classifier import AffairClassifier
from app.db.database import SessionLocal
from app.models.entities import Affair
from scripts.classify_affairs import (
    classify_batch,
    load_fallback_category,
    persist_batch,
)


API_URL = "https://api.openparldata.ch/v1/affairs/"
PAGE_SIZE = 20


@dataclass
class Checkpoint:
    updated_at: datetime
    record_id: int


def parse_datetime(value) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        result = value
    else:
        result = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

    if result.tzinfo is not None:
        result = result.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

    return result


def load_checkpoint(db) -> Checkpoint:
    row = db.execute(
        text(
            """
            SELECT
                last_updated_at,
                last_id
            FROM sync_checkpoints
            WHERE dataset = 'affairs'
            """
        )
    ).first()

    if row is None:
        raise RuntimeError(
            "Affairs checkpoint bulunamadi."
        )

    if row[0] is None or row[1] is None:
        raise RuntimeError(
            "Affairs checkpoint eksik."
        )

    return Checkpoint(
        updated_at=row[0],
        record_id=row[1],
    )


def is_after_checkpoint(
    record: dict,
    checkpoint: Checkpoint,
) -> bool:
    updated_at = parse_datetime(
        record.get("updated_at")
    )

    record_id = record.get("id")

    if updated_at is None or record_id is None:
        return False

    return (
        updated_at > checkpoint.updated_at
        or (
            updated_at == checkpoint.updated_at
            and record_id > checkpoint.record_id
        )
    )


def map_affair(record: dict) -> dict:
    values = {
        "id": record["id"],
    }

    direct_fields = (
        "body_id",
        "body_key",
        "number",
        "external_id",
        "external_alternative_id",
        "active",
    )

    for field in direct_fields:
        if field in record:
            values[field] = record[field]

    date_fields = (
        "begin_date",
        "end_date",
        "created_at",
        "updated_at",
    )

    for field in date_fields:
        if field in record:
            values[field] = parse_datetime(
                record[field]
            )

    language_fields = {
        "title": ("de", "fr", "it", "rm"),
        "title_long": ("de", "fr", "it", "rm"),
        "type_name": ("de", "fr", "it"),
        "type_harmonized": (
            "de",
            "fr",
            "it",
            "en",
        ),
        "state_name": (
            "de",
            "fr",
            "it",
        ),
        "state_name_harmonized": (
            "de",
            "fr",
            "it",
        ),
        "url_external": (
            "de",
            "fr",
            "it",
        ),
    }

    for source_field, languages in (
        language_fields.items()
    ):
        if source_field not in record:
            continue

        translations = record[source_field]

        if translations is None:
            translations = {}

        if not isinstance(
            translations,
            dict,
        ):
            raise ValueError(
                f"Affair {record['id']}: "
                f"{source_field} is not "
                "a language dictionary"
            )

        for language in languages:
            values[
                f"{source_field}_{language}"
            ] = translations.get(language)

    return values


def affair_values_changed(
    affair: Affair,
    values: dict,
) -> bool:
    for field, value in values.items():
        if field == "id":
            continue

        if getattr(affair, field) != value:
            return True

    return False


def update_affair(
    affair: Affair,
    values: dict,
) -> bool:
    changed = False

    for field, value in values.items():
        if field == "id":
            continue

        if getattr(affair, field) != value:
            setattr(
                affair,
                field,
                value,
            )
            changed = True

    return changed


def classify_new_affair(
    db,
    affair: Affair,
) -> None:
    classifier = AffairClassifier(db)

    fallback_category = (
        load_fallback_category(db)
    )

    (
        classification_rows,
        accepted_matches,
        _stats,
        _text_count,
    ) = classify_batch(
        db,
        classifier=classifier,
        affairs=[affair],
        fallback_category=fallback_category,
    )

    if not classification_rows:
        raise RuntimeError(
            f"Affair {affair.id}: "
            "classification missing"
        )

    persist_batch(
        db,
        classification_rows=classification_rows,
        accepted_matches=accepted_matches,
    )


def update_checkpoint(
    db,
    *,
    updated_at: datetime,
    record_id: int,
    status: str,
    records_processed: int,
    records_new: int,
    records_changed: int,
    records_unchanged: int,
    records_error: int,
    error_message: str | None = None,
) -> None:
    db.execute(
        text(
            """
            UPDATE sync_checkpoints
            SET
                last_updated_at = :updated_at,
                last_id = :record_id,
                last_run_at = :run_at,
                status = :status,
                records_processed = :processed,
                records_new = :new,
                records_changed = :changed,
                records_unchanged = :unchanged,
                records_error = :errors,
                error_message = :error_message
            WHERE dataset = 'affairs'
            """
        ),
        {
            "updated_at": updated_at,
            "record_id": record_id,
            "run_at": datetime.now(
                timezone.utc
            ).replace(tzinfo=None),
            "status": status,
            "processed": records_processed,
            "new": records_new,
            "changed": records_changed,
            "unchanged": records_unchanged,
            "errors": records_error,
            "error_message": error_message,
        },
    )


def process_affair(
    record: dict,
) -> str:
    values = map_affair(record)

    with SessionLocal() as db:
        try:
            affair = db.get(
                Affair,
                values["id"],
            )

            if affair is None:
                affair = Affair(
                    **values
                )

                db.add(affair)
                db.flush()

                classify_new_affair(
                    db,
                    affair,
                )

                db.commit()

                return "NEW_CLASSIFIED"

            if not affair_values_changed(
                affair,
                values,
            ):
                db.rollback()
                return "UNCHANGED"

            update_affair(
                affair,
                values,
            )

            db.commit()

            return "CHANGED"

        except Exception:
            db.rollback()
            raise


def fetch_page(
    client: httpx.Client,
    offset: int,
) -> list[dict]:
    response = client.get(
        API_URL,
        params={
            "offset": offset,
            "limit": PAGE_SIZE,
            "sort_by": "-updated_at,-id",
        },
    )

    response.raise_for_status()

    payload = response.json()

    return payload.get(
        "data",
        [],
    )


def main() -> None:
    with SessionLocal() as db:
        checkpoint = load_checkpoint(db)

    print("=" * 72)
    print("INCREMENTAL AFFAIR SYNC")
    print("=" * 72)

    print(
        "Checkpoint:",
        checkpoint.updated_at,
        checkpoint.record_id,
    )

    counts = {
        "NEW_CLASSIFIED": 0,
        "CHANGED": 0,
        "UNCHANGED": 0,
        "ERROR": 0,
    }

    offset = 0
    api_records = 0

    with httpx.Client(
        timeout=30,
        follow_redirects=True,
    ) as client:

        while True:
            records = fetch_page(
                client,
                offset,
            )

            if not records:
                break

            for record in records:
                api_records += 1

                if not is_after_checkpoint(
                    record,
                    checkpoint,
                ):
                    print(
                        "CHECKPOINT REACHED:",
                        record["id"],
                        record.get("updated_at"),
                    )

                    print()
                    print("=" * 72)
                    print("SYNC SONUCU")
                    print("=" * 72)
                    print(
                        "API kayitlari:",
                        api_records,
                    )
                    print(
                        "NEW:",
                        counts["NEW_CLASSIFIED"],
                    )
                    print(
                        "CHANGED:",
                        counts["CHANGED"],
                    )
                    print(
                        "UNCHANGED:",
                        counts["UNCHANGED"],
                    )
                    print(
                        "ERROR:",
                        counts["ERROR"],
                    )

                    return

                affair_id = record["id"]

                try:
                    status = process_affair(
                        record
                    )

                    counts[status] += 1

                    print(
                        f"Affair {affair_id}: "
                        f"{status}"
                    )

                except Exception as exc:
                    counts["ERROR"] += 1

                    print(
                        f"Affair {affair_id}: "
                        f"ERROR - {exc}"
                    )

                    print()
                    print(
                        "Checkpoint ilerletilmedi."
                    )

                    return

                updated_at = parse_datetime(
                    record.get("updated_at")
                )

                if updated_at is None:
                    raise RuntimeError(
                        f"Affair {affair_id}: "
                        "updated_at missing"
                    )

                with SessionLocal() as checkpoint_db:
                    update_checkpoint(
                        checkpoint_db,
                        updated_at=updated_at,
                        record_id=affair_id,
                        status="idle",
                        records_processed=(
                            sum(counts.values())
                        ),
                        records_new=(
                            counts[
                                "NEW_CLASSIFIED"
                            ]
                        ),
                        records_changed=(
                            counts["CHANGED"]
                        ),
                        records_unchanged=(
                            counts[
                                "UNCHANGED"
                            ]
                        ),
                        records_error=(
                            counts["ERROR"]
                        ),
                    )

                    checkpoint_db.commit()

            offset += PAGE_SIZE

    print()
    print("=" * 72)
    print("SYNC SONUCU")
    print("=" * 72)
    print(
        "API kayitlari:",
        api_records,
    )
    print(
        "NEW:",
        counts["NEW_CLASSIFIED"],
    )
    print(
        "CHANGED:",
        counts["CHANGED"],
    )
    print(
        "UNCHANGED:",
        counts["UNCHANGED"],
    )
    print(
        "ERROR:",
        counts["ERROR"],
    )


if __name__ == "__main__":
    main()