
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, text

from app.db.database import SessionLocal
from app.models.entities import Document


API_URL = "https://api.openparldata.ch/v1/docs/"
DATASET = "docs"
PAGE_SIZE = 500

INITIAL_UPDATED_AT = datetime(2026, 10, 8, 3, 4, 37)
INITIAL_ID = 927711

DIRECT_FIELDS = (
    "body_id",
    "body_key",
    "external_id",
    "name",
    "parent_type",
    "hash",
    "url",
    "url_oparl",
    "size",
    "category_harmonized",
    "format",
    "language",
    "text",
    "affair_id",
    "meeting_id",
    "agenda_id",
)

DATE_FIELDS = (
    "date",
    "updated_at",
)

LANGUAGE_FIELDS = {
    "category": ("de", "fr", "it"),
}


@dataclass
class Checkpoint:
    updated_at: datetime
    record_id: int


def parse_datetime(value):
    if value is None or value == "":
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


def map_document(record: dict) -> dict:
    values = {
        "source_id": int(record["id"])
    }

    for field in DIRECT_FIELDS:
        if field in record:
            values[field] = record[field]

    for field in DATE_FIELDS:
        if field in record:
            values[field] = parse_datetime(
                record[field]
            )

    for source_field, languages in LANGUAGE_FIELDS.items():
        if source_field not in record:
            continue

        translations = record[source_field]

        if translations is None:
            translations = {}

        if not isinstance(translations, dict):
            raise ValueError(
                f"Document {record['id']}: "
                f"{source_field} is not a language dictionary"
            )

        for language in languages:
            values[f"{source_field}_{language}"] = (
                translations.get(language)
            )

    return values


def get_checkpoint() -> Checkpoint:
    with SessionLocal() as db:
        row = db.execute(
            text(
                """
                SELECT last_updated_at, last_id
                FROM sync_checkpoints
                WHERE dataset = :dataset
                """
            ),
            {"dataset": DATASET},
        ).first()

        if row is None:
            db.execute(
                text(
                    """
                    INSERT INTO sync_checkpoints (
                        dataset,
                        last_updated_at,
                        last_id,
                        status
                    )
                    VALUES (
                        :dataset,
                        :updated_at,
                        :record_id,
                        'idle'
                    )
                    ON CONFLICT (dataset) DO NOTHING
                    """
                ),
                {
                    "dataset": DATASET,
                    "updated_at": INITIAL_UPDATED_AT,
                    "record_id": INITIAL_ID,
                },
            )
            db.commit()

            row = db.execute(
                text(
                    """
                    SELECT last_updated_at, last_id
                    FROM sync_checkpoints
                    WHERE dataset = :dataset
                    """
                ),
                {"dataset": DATASET},
            ).first()

        if row is None or row[0] is None:
            raise RuntimeError(
                "Document checkpoint bulunamadi."
            )

        return Checkpoint(
            updated_at=parse_datetime(row[0]),
            record_id=int(row[1] or 0),
        )


def save_checkpoint(
    checkpoint: Checkpoint,
    counts: dict,
    status: str,
    error_message: str | None = None,
) -> None:
    with SessionLocal() as db:
        db.execute(
            text(
                """
                UPDATE sync_checkpoints
                SET
                    last_updated_at = :updated_at,
                    last_id = :record_id,
                    last_run_at = CURRENT_TIMESTAMP,
                    status = :status,
                    records_processed = :processed,
                    records_new = :new,
                    records_changed = :changed,
                    records_unchanged = :unchanged,
                    records_error = :errors,
                    error_message = :error_message
                WHERE dataset = :dataset
                """
            ),
            {
                "dataset": DATASET,
                "updated_at": checkpoint.updated_at,
                "record_id": checkpoint.record_id,
                "status": status,
                "processed": (
                    counts["NEW"]
                    + counts["CHANGED"]
                    + counts["UNCHANGED"]
                ),
                "new": counts["NEW"],
                "changed": counts["CHANGED"],
                "unchanged": counts["UNCHANGED"],
                "errors": counts["ERROR"],
                "error_message": error_message,
            },
        )
        db.commit()


def record_cursor(record: dict) -> tuple[datetime, int]:
    updated_at = parse_datetime(
        record.get("updated_at")
    )

    if updated_at is None:
        raise ValueError(
            f"Document {record.get('id')}: updated_at eksik."
        )

    return updated_at, int(record["id"])


def fetch_page(
    client: httpx.Client,
    offset: int,
) -> list[dict]:
    response = client.get(
        API_URL,
        params={
            "limit": PAGE_SIZE,
            "offset": offset,
            "sort_by": "-updated_at,-id",
        },
    )

    response.raise_for_status()

    records = response.json().get("data")

    if not isinstance(records, list):
        raise RuntimeError(
            "API response: data listesi bulunamadi."
        )

    return records


def sync_one_document(
    record: dict,
) -> tuple[str, list[str]]:
    values = map_document(record)

    with SessionLocal() as db:
        try:
            document = db.scalar(
                select(Document).where(
                    Document.source_id
                    == values["source_id"]
                )
            )

            if document is None:
                db.add(Document(**values))
                db.commit()
                return "NEW", []

            changed_fields = []

            for field, value in values.items():
                if field in (
                    "source_id",
                    "updated_at",
                ):
                    continue

                if getattr(document, field) != value:
                    setattr(document, field, value)
                    changed_fields.append(field)

            if changed_fields:
                if "updated_at" in values:
                    document.updated_at = (
                        values["updated_at"]
                    )

                db.commit()
                return "CHANGED", changed_fields

            if (
                "updated_at" in values
                and document.updated_at != values["updated_at"]
            ):
                document.updated_at = values["updated_at"]
                db.commit()
            else:
                db.rollback()

            return "UNCHANGED", []

        except Exception:
            db.rollback()
            raise


def run_sync(recheck: bool = False) -> None:
    from scripts.sync.entity_sync import run_dataset
    run_dataset("documents", recheck=recheck)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--recheck",
        action="store_true",
        help="Eski Document kayitlarini da kontrol et.",
    )

    args = parser.parse_args()
    run_sync(recheck=args.recheck)


if __name__ == "__main__":
    main()
