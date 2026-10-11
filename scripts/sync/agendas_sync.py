
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from app.db.database import SessionLocal
from app.models.entities import Agenda
from app.services.change_event_service import create_change_event


API_URL = "https://api.openparldata.ch/v1/agendas/"
DATASET = "agendas"
PAGE_SIZE = 500

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


def normalize_for_hash(value):
    if isinstance(value, datetime):
        return value.isoformat()

    return value


def calculate_fingerprint(agenda: Agenda) -> str:
    payload = {
        field: normalize_for_hash(
            getattr(agenda, field)
        )
        for field in FINGERPRINT_FIELDS
    }

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def get_checkpoint() -> int:
    with SessionLocal() as db:
        row = db.execute(
            text(
                """
                SELECT last_id
                FROM sync_checkpoints
                WHERE dataset = :dataset
                """
            ),
            {"dataset": DATASET},
        ).first()

        if row is not None:
            return int(row[0] or 0)

        db.execute(
            text(
                """
                INSERT INTO sync_checkpoints (
                    dataset,
                    last_id,
                    status
                )
                VALUES (
                    :dataset,
                    :last_id,
                    'idle'
                )
                ON CONFLICT (dataset) DO NOTHING
                """
            ),
            {
                "dataset": DATASET,
                "last_id": INITIAL_LAST_ID,
            },
        )
        db.commit()

        row = db.execute(
            text(
                """
                SELECT last_id
                FROM sync_checkpoints
                WHERE dataset = :dataset
                """
            ),
            {"dataset": DATASET},
        ).first()

        if row is None:
            raise RuntimeError(
                "Agenda checkpoint olusturulamadi."
            )

        return int(row[0] or 0)


def save_checkpoint(
    last_id: int,
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
                    last_id = :last_id,
                    last_run_at = CURRENT_TIMESTAMP,
                    status = :status,
                    records_processed = :records_processed,
                    records_new = :records_new,
                    records_changed = :records_changed,
                    records_unchanged = :records_unchanged,
                    records_error = :records_error,
                    error_message = :error_message
                WHERE dataset = :dataset
                """
            ),
            {
                "dataset": DATASET,
                "last_id": last_id,
                "status": status,
                "records_processed": (
                    counts["NEW"]
                    + counts["CHANGED"]
                    + counts["UNCHANGED"]
                ),
                "records_new": counts["NEW"],
                "records_changed": counts["CHANGED"],
                "records_unchanged": counts["UNCHANGED"],
                "records_error": counts["ERROR"],
                "error_message": error_message,
            },
        )
        db.commit()


def fetch_page(
    client: httpx.Client,
    offset: int,
) -> list[dict]:
    response = client.get(
        API_URL,
        params={
            "limit": PAGE_SIZE,
            "offset": offset,
            "sort_by": "-id",
        },
    )

    response.raise_for_status()

    records = response.json().get("data")

    if not isinstance(records, list):
        raise RuntimeError(
            "API response: data listesi bulunamadi."
        )

    return records


def sync_one_agenda(record: dict) -> str:
    values = map_agenda(record)

    with SessionLocal() as db:
        try:
            agenda = db.get(
                Agenda,
                values["id"],
            )

            if agenda is None:
                agenda = Agenda(**values)
                db.add(agenda)
                db.flush()

                fingerprint = calculate_fingerprint(
                    agenda
                )

                create_change_event(
                    db,
                    dataset=DATASET,
                    source_id=agenda.id,
                    affair_id=agenda.item_affair_id,
                    change_type="created",
                    fingerprint=fingerprint,
                    description="New agenda detected.",
                )

                db.commit()
                return "NEW"

            changed_fields = []

            for field, value in values.items():
                if field in ("id", "created_at"):
                    continue

                if getattr(agenda, field) != value:
                    setattr(agenda, field, value)
                    changed_fields.append(field)

            if changed_fields:
                fingerprint = calculate_fingerprint(
                    agenda
                )

                create_change_event(
                    db,
                    dataset=DATASET,
                    source_id=agenda.id,
                    affair_id=agenda.item_affair_id,
                    change_type="updated",
                    fingerprint=fingerprint,
                    description=(
                        "Changed fields: "
                        + ", ".join(changed_fields)
                    ),
                )

                db.commit()

                return (
                    "CHANGED: "
                    + ", ".join(changed_fields)
                )

            db.rollback()
            return "UNCHANGED"

        except Exception:
            db.rollback()
            raise


def run_sync(recheck: bool = False) -> None:
    from scripts.sync.entity_sync import run_dataset
    run_dataset("agendas", recheck=recheck)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--recheck",
        action="store_true",
        help="Eski Agenda kayitlarini da kontrol et.",
    )

    args = parser.parse_args()
    run_sync(recheck=args.recheck)


if __name__ == "__main__":
    main()
