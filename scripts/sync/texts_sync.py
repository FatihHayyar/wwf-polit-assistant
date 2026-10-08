
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from app.db.database import SessionLocal
from app.models.entities import ParliamentaryText


API_URL = "https://api.openparldata.ch/v1/texts/"
DATASET = "texts"
PAGE_SIZE = 500

INITIAL_CREATED_AT = datetime(2026, 10, 5, 21, 25, 49)
INITIAL_ID = 225724

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


@dataclass
class Checkpoint:
    created_at: datetime
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
                        :created_at,
                        :record_id,
                        'idle'
                    )
                    ON CONFLICT (dataset) DO NOTHING
                    """
                ),
                {
                    "dataset": DATASET,
                    "created_at": INITIAL_CREATED_AT,
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
                "Text checkpoint bulunamadi."
            )

        return Checkpoint(
            created_at=parse_datetime(row[0]),
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
                    last_updated_at = :created_at,
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
                "created_at": checkpoint.created_at,
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
    created_at = parse_datetime(
        record.get("created_at")
    )

    if created_at is None:
        raise ValueError(
            f"Text {record.get('id')}: created_at eksik."
        )

    return created_at, int(record["id"])


def fetch_page(
    client: httpx.Client,
    offset: int,
) -> list[dict]:
    response = client.get(
        API_URL,
        params={
            "limit": PAGE_SIZE,
            "offset": offset,
            "sort_by": "-created_at,-id",
        },
    )

    response.raise_for_status()

    records = response.json().get("data")

    if not isinstance(records, list):
        raise RuntimeError(
            "API response: data listesi bulunamadi."
        )

    return records


def sync_one_text(
    record: dict,
) -> tuple[str, list[str]]:
    values = map_text(record)

    with SessionLocal() as db:
        try:
            parliamentary_text = db.get(
                ParliamentaryText,
                values["id"],
            )

            if parliamentary_text is None:
                db.add(ParliamentaryText(**values))
                db.commit()
                return "NEW", []

            changed_fields = []

            for field, value in values.items():
                if field in (
                    "id",
                    "created_at",
                    "updated_at",
                ):
                    continue

                if (
                    getattr(parliamentary_text, field)
                    != value
                ):
                    setattr(
                        parliamentary_text,
                        field,
                        value,
                    )
                    changed_fields.append(field)

            if changed_fields:
                if "updated_at" in values:
                    parliamentary_text.updated_at = (
                        values["updated_at"]
                    )

                db.commit()
                return "CHANGED", changed_fields

            if (
                "updated_at" in values
                and parliamentary_text.updated_at
                != values["updated_at"]
            ):
                parliamentary_text.updated_at = (
                    values["updated_at"]
                )
                db.commit()
            else:
                db.rollback()

            return "UNCHANGED", []

        except Exception:
            db.rollback()
            raise


def run_sync(recheck: bool = False) -> None:
    original = get_checkpoint()

    original_cursor = (
        original.created_at,
        original.record_id,
    )

    counts = {
        "NEW": 0,
        "CHANGED": 0,
        "UNCHANGED": 0,
        "ERROR": 0,
    }

    pages = 0
    scanned = 0
    offset = 0
    newest_cursor = None
    run_upper_cursor = None

    print("=" * 64, flush=True)
    print("TEXT INCREMENTAL SYNC", flush=True)
    print("=" * 64, flush=True)
    print(
        f"Mod: {'FULL RECHECK' if recheck else 'NEW RECORDS'}",
        flush=True,
    )
    print(
        "Baslangic checkpoint:",
        original.created_at,
        original.record_id,
        flush=True,
    )

    try:
        with httpx.Client(
            timeout=60,
            follow_redirects=True,
        ) as client:
            while True:
                records = fetch_page(client, offset)
                pages += 1

                if not records:
                    break

                if run_upper_cursor is None:
                    run_upper_cursor = record_cursor(
                        records[0]
                    )

                print(
                    f"\n[SAYFA {pages}] "
                    f"offset={offset} "
                    f"kayit={len(records)}",
                    flush=True,
                )

                reached_checkpoint = False

                for record in records:
                    cursor = record_cursor(record)
                    scanned += 1

                    if cursor > run_upper_cursor:
                        continue

                    if (
                        not recheck
                        and cursor <= original_cursor
                    ):
                        reached_checkpoint = True
                        break

                    status, changed_fields = sync_one_text(
                        record
                    )

                    counts[status] += 1

                    if (
                        newest_cursor is None
                        or cursor > newest_cursor
                    ):
                        newest_cursor = cursor

                    processed = (
                        counts["NEW"]
                        + counts["CHANGED"]
                        + counts["UNCHANGED"]
                    )

                    print(
                        f"[{processed}] "
                        f"Text {record['id']}: {status}",
                        flush=True,
                    )

                    if changed_fields:
                        print(
                            "    Changed:",
                            ", ".join(changed_fields),
                            flush=True,
                        )

                    if processed % 100 == 0:
                        print(
                            "--- ILERLEME: "
                            f"islenen={processed}, "
                            f"NEW={counts['NEW']}, "
                            f"CHANGED={counts['CHANGED']}, "
                            f"UNCHANGED={counts['UNCHANGED']}",
                            flush=True,
                        )

                if reached_checkpoint:
                    break

                if len(records) < PAGE_SIZE:
                    break

                offset += PAGE_SIZE

    except BaseException as exc:
        counts["ERROR"] += 1

        save_checkpoint(
            original,
            counts,
            status="error",
            error_message=str(exc),
        )

        print(
            f"\nSYNC DURDU: {exc}",
            flush=True,
        )
        print(
            "Checkpoint ilerletilmedi.",
            flush=True,
        )
        raise

    if newest_cursor is not None:
        final = Checkpoint(
            created_at=newest_cursor[0],
            record_id=newest_cursor[1],
        )
    else:
        final = original

    save_checkpoint(
        final,
        counts,
        status="idle",
    )

    print("\n" + "=" * 64, flush=True)
    print("TEXT SYNC SONUCU", flush=True)
    print("=" * 64, flush=True)
    print(f"API sayfalari: {pages}", flush=True)
    print(f"Taranan: {scanned}", flush=True)
    print(
        "Islenen:",
        counts["NEW"]
        + counts["CHANGED"]
        + counts["UNCHANGED"],
        flush=True,
    )
    print(f"NEW: {counts['NEW']}", flush=True)
    print(f"CHANGED: {counts['CHANGED']}", flush=True)
    print(f"UNCHANGED: {counts['UNCHANGED']}", flush=True)
    print(f"ERROR: {counts['ERROR']}", flush=True)
    print(
        "Yeni checkpoint:",
        final.created_at,
        final.record_id,
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--recheck",
        action="store_true",
        help="Eski Text kayitlarini da kontrol et.",
    )

    args = parser.parse_args()
    run_sync(recheck=args.recheck)


if __name__ == "__main__":
    main()
