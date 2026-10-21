
from __future__ import annotations

import argparse
from datetime import datetime, timezone




API_URL = "https://api.openparldata.ch/v1/texts/"


DIRECT_FIELDS = (
    "body_id",
    "body_key",
    "external_id",
    "affair_id",
    "text_format",
)

DATE_FIELDS = (
    "text_date",
    "created_at",
    "updated_at",
)

LANGUAGE_FIELDS = {
    "type": ("de", "fr", "it", "rm"),
    "text": ("de", "fr", "it", "rm"),
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


def map_text(record: dict) -> dict:
    values = {"id": int(record["id"])}

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
                f"Text {record['id']}: "
                f"{source_field} is not a language dictionary"
            )

        for language in languages:
            values[f"{source_field}_{language}"] = (
                translations.get(language)
            )

    return values


def run_sync(recheck: bool = False) -> None:
    from scripts.sync.entity_sync import run_dataset
    run_dataset("texts", recheck=recheck)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--recheck",
        action="store_true",
        help="Compare every text record instead of an incremental run.",
    )

    args = parser.parse_args()
    run_sync(recheck=args.recheck)


if __name__ == "__main__":
    main()
