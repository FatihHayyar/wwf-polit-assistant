
from __future__ import annotations

import argparse
from datetime import datetime, timezone




API_URL = "https://api.openparldata.ch/v1/votings/"


DIRECT_FIELDS = (
    "body_id",
    "body_key",
    "external_id",
    "affair_id",
    "meeting_id",
    "group_id",
    "results_yes",
    "results_no",
    "results_abstention",
    "results_absent",
    "results_string",
    "decision",
)

DATE_FIELDS = (
    "date",
    "created_at",
    "updated_at",
)

LANGUAGE_FIELDS = {
    "title": ("de", "fr", "it"),
    "type": ("de", "fr", "it"),
    "meaning_of_yes": ("de", "fr", "it"),
    "meaning_of_no": ("de", "fr", "it"),
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


def map_voting(record: dict) -> dict:
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
                f"Voting {record['id']}: "
                f"{source_field} is not a language dictionary"
            )

        for language in languages:
            values[f"{source_field}_{language}"] = (
                translations.get(language)
            )

    return values


def run_sync(recheck: bool = False) -> None:
    from scripts.sync.entity_sync import run_dataset
    run_dataset("votings", recheck=recheck)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--recheck",
        action="store_true",
        help="Compare every voting record instead of an incremental run.",
    )

    args = parser.parse_args()
    run_sync(recheck=args.recheck)


if __name__ == "__main__":
    main()
