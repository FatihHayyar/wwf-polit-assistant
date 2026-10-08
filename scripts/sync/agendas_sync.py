
from __future__ import annotations

import argparse
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from app.db.database import SessionLocal
from app.models.entities import Agenda


API_URL = "https://api.openparldata.ch/v1/agendas/"
DATASET = "agendas"
PAGE_SIZE = 500

# Daha once kontrol ettigimiz DB max Agenda ID.
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

        # Ilk calismada mevcut DB max ID'den basla.
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
                db.add(Agenda(**values))
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
    original_checkpoint = get_checkpoint()

    counts = {
        "NEW": 0,
        "CHANGED": 0,
        "UNCHANGED": 0,
        "ERROR": 0,
    }

    offset = 0
    pages = 0
    scanned = 0
    newest_id = original_checkpoint

    # Ilk sayfanin en yuksek ID'si.
    # Sync sirasinda yeni gelen kayitlari
    # sonraki calismaya birakiyoruz.
    run_upper_id = None

    print("=" * 64, flush=True)
    print("AGENDA INCREMENTAL SYNC", flush=True)
    print("=" * 64, flush=True)
    print(
        f"Mod: {'FULL RECHECK' if recheck else 'NEW RECORDS'}",
        flush=True,
    )
    print(
        f"Baslangic checkpoint: {original_checkpoint}",
        flush=True,
    )

    try:
        with httpx.Client(
            timeout=60,
            follow_redirects=True,
        ) as client:
            while True:
                records = fetch_page(
                    client,
                    offset,
                )

                pages += 1

                if not records:
                    break

                if run_upper_id is None:
                    run_upper_id = int(records[0]["id"])

                print(
                    f"\n[SAYFA {pages}] "
                    f"offset={offset}, "
                    f"kayit={len(records)}",
                    flush=True,
                )

                reached_checkpoint = False

                for record in records:
                    agenda_id = int(record["id"])
                    scanned += 1

                    if agenda_id > run_upper_id:
                        continue

                    if (
                        not recheck
                        and agenda_id <= original_checkpoint
                    ):
                        reached_checkpoint = True
                        break

                    status = sync_one_agenda(record)
                    status_key = status.split(":")[0]
                    counts[status_key] += 1

                    if agenda_id > newest_id:
                        newest_id = agenda_id

                    print(
                        f"Agenda {agenda_id}: {status}",
                        flush=True,
                    )

                    processed = (
                        counts["NEW"]
                        + counts["CHANGED"]
                        + counts["UNCHANGED"]
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
            last_id=original_checkpoint,
            counts=counts,
            status="error",
            error_message=str(exc),
        )

        print(
            f"\nSYNC ERROR: {exc}",
            flush=True,
        )
        print(
            "Checkpoint ilerletilmedi.",
            flush=True,
        )
        raise

    save_checkpoint(
        last_id=newest_id,
        counts=counts,
        status="idle",
    )

    print("\n" + "=" * 64, flush=True)
    print("AGENDA SYNC SONUCU", flush=True)
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
        f"Yeni checkpoint: {newest_id}",
        flush=True,
    )


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
