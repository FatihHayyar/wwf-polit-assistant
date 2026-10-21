
from __future__ import annotations

import argparse
from datetime import datetime, timezone




API_URL = "https://api.openparldata.ch/v1/agendas/"

# Mevcut veritabanindan belirlenen baslangic ID'si.
INITIAL_LAST_ID = 431492

FIELDS = (
    "body_id",
    "body_key",
    "meeting_id",
    "item_date",
    "item_external_id",
    "item_title",
    "item_number_display",
    "item_number",
    "item_description",
    "item_status",
    "item_result",
    "item_category",
    "item_url",
    "item_affair_number",
    "item_affair_id",
    "item_language",
    "created_at",
)

DATE_FIELDS = {
    "item_date",
    "created_at",
}

# Kaydin gercek icerigini temsil eden alanlar.
# created_at fingerprint'e dahil edilmez.
FINGERPRINT_FIELDS = tuple(
    field for field in FIELDS
    if field != "created_at"
)


def parse_datetime(value):
    if not value:
        return None

    result = datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    )

    if result.tzinfo is not None:
        result = result.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

    return result


def map_agenda(record: dict) -> dict:
    values = {"id": int(record["id"])}

    for field in FIELDS:
        if field not in record:
            continue

        value = record[field]

        if field in DATE_FIELDS:
            value = parse_datetime(value)

        values[field] = value

    return values


def run_sync(recheck: bool = False) -> None:
    from scripts.sync.entity_sync import run_dataset
    run_dataset("agendas", recheck=recheck)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--recheck",
        action="store_true",
        help="Compare every agenda record instead of an incremental run.",
    )

    args = parser.parse_args()
    run_sync(recheck=args.recheck)


if __name__ == "__main__":
    main()
