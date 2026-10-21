
from __future__ import annotations

import argparse
from datetime import datetime, timezone




API_URL = "https://api.openparldata.ch/v1/events/"


DIRECT_FIELDS = (
    "body_id",
    "body_key",
    "external_id",
    "position",
    "last",
    "actor_type",
    "affair_id",
    "meeting_id",
    "details_url",
    "details_text",
)

DATE_FIELDS = (
    "date",
    "created_at",
    "updated_at",
)

LANGUAGE_FIELDS = {
    "title": ("de", "fr", "it"),
    "title_harmonized": ("de", "fr", "it", "en"),
    "actor": ("de", "fr", "it"),
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


def map_event(record: dict) -> dict:
    values = {"id": int(record["id"])}

    for field in DIRECT_FIELDS:
        if field in record:
            values[field] = record[field]

    for field in DATE_FIELDS:
        if field in record:
            values[field] = parse_datetime(record[field])

    for source_field, languages in LANGUAGE_FIELDS.items():
        # Exports can expose translations as flat fields; the live API returns
        # title_harmonized as a scalar label instead of a translation object.
        for language in languages:
            field = f"{source_field}_{language}"
            if field in record:
                values[field] = record[field]
        if source_field not in record:
            continue

        translations = record[source_field]

        if source_field == "title_harmonized" and isinstance(translations, str):
            # Missing translations are unspecified, not deleted. Preserve the
            # translations already imported from the bulk export. The scalar
            # label adds no translated content and is not a content change.
            continue

        if translations is None:
            translations = {}

        if not isinstance(translations, dict):
            raise ValueError(
                f"Event {record['id']}: "
                f"{source_field} is not a language dictionary"
            )

        for language in languages:
            field = f"{source_field}_{language}"
            if field not in record:
                values[field] = translations.get(language)

    return values


def run_sync(recheck: bool = False) -> None:
    from scripts.sync.entity_sync import run_dataset
    run_dataset("events", recheck=recheck)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--recheck",
        action="store_true",
        help="Compare every event record instead of an incremental run.",
    )

    args = parser.parse_args()
    run_sync(recheck=args.recheck)


if __name__ == "__main__":
    main()
