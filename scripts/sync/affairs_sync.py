
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.classification.classifier import AffairClassifier
from app.db.database import SessionLocal
from app.models.entities import Affair
from scripts.classify_affairs import (
    classify_batch,
    load_fallback_category,
    persist_batch,
)

API_URL = "https://api.openparldata.ch/v1/affairs/"
BATCH_SIZE = 20

LANGUAGE_FIELDS = {
    "title": ("de", "fr", "it", "rm"),
    "title_long": ("de", "fr", "it", "rm"),
    "type_name": ("de", "fr", "it"),
    "type_harmonized": ("de", "fr", "it", "en"),
    "state_name": ("de", "fr", "it"),
    "state_name_harmonized": ("de", "fr", "it"),
    "url_external": ("de", "fr", "it"),
}

DIRECT_FIELDS = (
    "body_id",
    "body_key",
    "number",
    "external_id",
    "external_alternative_id",
    "active",
)

DATE_FIELDS = (
    "begin_date",
    "end_date",
    "created_at",
    "updated_at",
)


def parse_datetime(value):
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


def map_affair(record: dict) -> dict:
    values = {"id": record["id"]}

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
                f"Affair {record['id']}: "
                f"{source_field} is not a language dictionary"
            )

        for language in languages:
            values[f"{source_field}_{language}"] = (
                translations.get(language)
            )

    return values


def fetch_affairs() -> list[dict]:
    with httpx.Client(timeout=30) as client:
        response = client.get(
            API_URL,
            params={
                "limit": BATCH_SIZE,
                "sort_by": "-updated_at,-id",
            },
        )

        response.raise_for_status()
        return response.json()["data"]


def sync_one_affair(record: dict) -> str:
    values = map_affair(record)

    with SessionLocal() as db:
        try:
            affair = db.get(
                Affair,
                values["id"],
            )

            # ---------------------------------
            # NEW AFFAIR
            # ---------------------------------
            if affair is None:
                affair = Affair(**values)

                db.add(affair)
                db.flush()

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

                # Affair and classification
                # committed together.
                db.commit()

                return "NEW_CLASSIFIED"

            # ---------------------------------
            # EXISTING AFFAIR
            # ---------------------------------
            changed_fields = []

            for field, value in values.items():
                if field in (
                    "id",
                    "created_at",
                    "updated_at",
                ):
                    continue

                if getattr(affair, field) != value:
                    changed_fields.append(field)
                    setattr(affair, field, value)

            if changed_fields:
                if "updated_at" in values:
                    affair.updated_at = (
                        values["updated_at"]
                    )

                db.commit()

                return (
                    "CHANGED: "
                    + ", ".join(changed_fields)
                )

            # Ignore timestamp-only changes.
            db.rollback()

            return "UNCHANGED"

        except Exception:
            db.rollback()
            raise


def main() -> None:
    records = fetch_affairs()

    counts = {
        "NEW_CLASSIFIED": 0,
        "CHANGED": 0,
        "UNCHANGED": 0,
        "ERROR": 0,
    }

    for record in records:
        affair_id = record.get("id")

        try:
            status = sync_one_affair(record)

        except Exception as exc:
            status = "ERROR"
            print(
                f"Affair {affair_id}: "
                f"ERROR - {exc}"
            )

        if status != "ERROR":
            print(
                f"Affair {affair_id}: "
                f"{status}"
            )

        # "CHANGED: title_de" -> "CHANGED"
        status_key = status.split(":")[0]

        counts[status_key] += 1

    print("\nSonuc:", counts)


if __name__ == "__main__":
    main()
