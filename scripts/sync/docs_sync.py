
from __future__ import annotations

import argparse
from datetime import datetime, timezone




API_URL = "https://api.openparldata.ch/v1/docs/"


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


def run_sync(recheck: bool = False) -> None:
    from scripts.sync.entity_sync import run_dataset
    run_dataset("documents", recheck=recheck)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--recheck",
        action="store_true",
        help="Compare every document record instead of an incremental run.",
    )

    args = parser.parse_args()
    run_sync(recheck=args.recheck)


if __name__ == "__main__":
    main()
