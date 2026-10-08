
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from app.services.change_event_service import create_change_event
import httpx
from sqlalchemy import text

from app.classification.classifier import AffairClassifier
from app.db.database import SessionLocal
from app.models.entities import Affair
from scripts.classify_affairs import (
    classify_batch,
    load_fallback_category,
    persist_batch,
)


API_URL = "https://api.openparldata.ch/v1/affairs/"
PAGE_SIZE = 500

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

FINGERPRINT_FIELDS = (
    "body_id",
    "body_key",
    "number",
    "external_id",
    "external_alternative_id",
    "title_de",
    "title_fr",
    "title_it",
    "title_rm",
    "title_long_de",
    "title_long_fr",
    "title_long_it",
    "title_long_rm",
    "type_name_de",
    "type_name_fr",
    "type_name_it",
    "type_harmonized_de",
    "type_harmonized_fr",
    "type_harmonized_it",
    "type_harmonized_en",
    "state_name_de",
    "state_name_fr",
    "state_name_it",
    "state_name_harmonized_de",
    "state_name_harmonized_fr",
    "state_name_harmonized_it",
    "active",
    "begin_date",
    "end_date",
    "url_external_de",
    "url_external_fr",
    "url_external_it",
)


@dataclass
class Checkpoint:
    updated_at: datetime | None
    record_id: int | None


@dataclass
class SyncResult:
    status: str
    changed_fields: list[str]


def parse_datetime(value: Any) -> datetime | None:
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


def map_affair(record: dict) -> dict:
    values = {"id": int(record["id"])}

    for field in DIRECT_FIELDS:
        if field in record:
            values[field] = record[field]

    for field in DATE_FIELDS:
        if field in record:
            values[field] = parse_datetime(record[field])

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


def normalize_for_hash(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): normalize_for_hash(value[key])
            for key in sorted(value)
        }

    if isinstance(value, (list, tuple)):
        return [
            normalize_for_hash(item)
            for item in value
        ]

    return value


def calculate_fingerprint(values: dict) -> str:
    payload = {
        field: normalize_for_hash(values.get(field))
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


def get_checkpoint() -> Checkpoint:
    with SessionLocal() as db:
        row = db.execute(
            text(
                """
                SELECT last_updated_at, last_id
                FROM sync_checkpoints
                WHERE dataset = 'affairs'
                """
            )
        ).first()

    if row is None:
        raise RuntimeError(
            "Affairs checkpoint bulunamadi."
        )

    return Checkpoint(
        updated_at=parse_datetime(row[0]),
        record_id=row[1],
    )


def set_checkpoint(
    checkpoint: Checkpoint,
    *,
    status: str,
    records_processed: int,
    records_new: int,
    records_changed: int,
    records_unchanged: int,
    records_error: int,
    error_message: str | None = None,
) -> None:
    with SessionLocal() as db:
        db.execute(
            text(
                """
                UPDATE sync_checkpoints
                SET
                    last_updated_at = :last_updated_at,
                    last_id = :last_id,
                    last_run_at = CURRENT_TIMESTAMP,
                    status = :status,
                    records_processed = :records_processed,
                    records_new = :records_new,
                    records_changed = :records_changed,
                    records_unchanged = :records_unchanged,
                    records_error = :records_error,
                    error_message = :error_message
                WHERE dataset = 'affairs'
                """
            ),
            {
                "last_updated_at": checkpoint.updated_at,
                "last_id": checkpoint.record_id,
                "status": status,
                "records_processed": records_processed,
                "records_new": records_new,
                "records_changed": records_changed,
                "records_unchanged": records_unchanged,
                "records_error": records_error,
                "error_message": error_message,
            },
        )
        db.commit()


def checkpoint_cursor(
    checkpoint: Checkpoint,
) -> tuple[datetime, int] | None:
    if checkpoint.updated_at is None:
        return None

    return (
        checkpoint.updated_at,
        int(checkpoint.record_id or 0),
    )


def record_cursor(
    record: dict,
) -> tuple[datetime, int]:
    updated_at = parse_datetime(
        record.get("updated_at")
    )

    if updated_at is None:
        raise ValueError(
            f"Affair {record.get('id')}: updated_at eksik"
        )

    return updated_at, int(record["id"])


def classify_new_affair(db, affair: Affair) -> None:
    classifier = AffairClassifier(db)
    fallback_category = load_fallback_category(db)

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
            f"Affair {affair.id}: classification missing"
        )

    persist_batch(
        db,
        classification_rows=classification_rows,
        accepted_matches=accepted_matches,
    )


def sync_one_affair(record: dict) -> SyncResult:
    values = map_affair(record)
    new_fingerprint = calculate_fingerprint(values)

    with SessionLocal() as db:
        try:
            affair = db.get(Affair, values["id"])

            if affair is None:
                affair = Affair(**values)
                affair.sync_fingerprint = new_fingerprint

                db.add(affair)
                db.flush()

                classify_new_affair(db, affair)

                create_change_event(
                     db,
                     affair_id=affair.id,
                     change_type="created",
                     fingerprint=new_fingerprint,
                     description="New affair detected.",
                )

                db.commit()

                return SyncResult(
                    status="NEW_CLASSIFIED",
                    changed_fields=[],
                )

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

            if changed_fields:
                for field in changed_fields:
                    setattr(affair, field, values[field])

                if "updated_at" in values:
                    affair.updated_at = values["updated_at"]

                affair.sync_fingerprint = new_fingerprint

                create_change_event(
                     db,
                     affair_id=affair.id,
                     change_type="updated",
                     fingerprint=new_fingerprint,
                     description="Changed fields: " + ", ".join(changed_fields),
                )

                db.commit()

                return SyncResult(
                    status="CHANGED",
                    changed_fields=changed_fields,
                )

            needs_commit = False

            if affair.sync_fingerprint != new_fingerprint:
                affair.sync_fingerprint = new_fingerprint
                needs_commit = True

            if (
                "updated_at" in values
                and affair.updated_at != values["updated_at"]
            ):
                affair.updated_at = values["updated_at"]
                needs_commit = True

            if needs_commit:
                db.commit()
            else:
                db.rollback()

            return SyncResult(
                status="UNCHANGED",
                changed_fields=[],
            )

        except Exception:
            db.rollback()
            raise


def fetch_page(
    client: httpx.Client,
    *,
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

    payload = response.json()
    records = payload.get("data")

    if not isinstance(records, list):
        raise RuntimeError(
            "API response: data listesi bulunamadi."
        )

    return records


def run_incremental_sync() -> None:
    print("=" * 72, flush=True)
    print("INCREMENTAL AFFAIR SYNC - GERCEK ISLEM", flush=True)
    print("=" * 72, flush=True)

    original_checkpoint = get_checkpoint()
    original_cursor = checkpoint_cursor(
        original_checkpoint
    )

    print(
        "Baslangic checkpoint:",
        original_checkpoint.updated_at,
        original_checkpoint.record_id,
        flush=True,
    )

    counts = {
        "NEW_CLASSIFIED": 0,
        "CHANGED": 0,
        "UNCHANGED": 0,
        "ERROR": 0,
    }

    pages = 0
    scanned = 0
    offset = 0
    reached_checkpoint = False

    # En yeni basarili kaydin cursor'u.
    # En eski islenen kaydi checkpoint yapmayacagiz.
    newest_cursor = None

    # API'deki ilk sayfanin en yeni cursor'u.
    # Bu calisma icin ust sinir olarak kullanilir.
    run_upper_cursor = None

    try:
        with httpx.Client(
            timeout=60,
            follow_redirects=True,
        ) as client:

            while True:
                page = fetch_page(
                    client,
                    offset=offset,
                )

                pages += 1

                if not page:
                    print(
                        "API kayitlari bitti.",
                        flush=True,
                    )
                    break

                if run_upper_cursor is None:
                    run_upper_cursor = record_cursor(page[0])

                print(
                    f"[SAYFA {pages}] "
                    f"offset={offset} "
                    f"gelen={len(page)} "
                    f"taranan={scanned}",
                    flush=True,
                )

                for record in page:
                    cursor = record_cursor(record)
                    scanned += 1

                    # Sync basladiktan sonra daha yeni
                    # timestamp alan kayitlari bu turda
                    # islemiyoruz.
                    if cursor > run_upper_cursor:
                        continue

                    if (
                        original_cursor is not None
                        and cursor <= original_cursor
                    ):
                        reached_checkpoint = True
                        break

                    result = sync_one_affair(record)
                    counts[result.status] += 1

                    if (
                        newest_cursor is None
                        or cursor > newest_cursor
                    ):
                        newest_cursor = cursor

                    processed = (
                        counts["NEW_CLASSIFIED"]
                        + counts["CHANGED"]
                        + counts["UNCHANGED"]
                    )

                    print(
                        f"[{processed}] "
                        f"Affair {record['id']}: "
                        f"{result.status}",
                        flush=True,
                    )

                    if result.changed_fields:
                        print(
                            "    Changed:",
                            ", ".join(result.changed_fields),
                            flush=True,
                        )

                    if processed % 100 == 0:
                        print(
                            "--- ILERLEME: "
                            f"sayfa={pages}, "
                            f"taranan={scanned}, "
                            f"islenen={processed}, "
                            f"NEW={counts['NEW_CLASSIFIED']}, "
                            f"CHANGED={counts['CHANGED']}, "
                            f"UNCHANGED={counts['UNCHANGED']}",
                            flush=True,
                        )

                if reached_checkpoint:
                    print(
                        "Checkpoint'e ulasildi.",
                        flush=True,
                    )
                    break

                if len(page) < PAGE_SIZE:
                    print(
                        "API son sayfasina ulasildi.",
                        flush=True,
                    )
                    break

                offset += PAGE_SIZE

    except BaseException as exc:
        # Ctrl+C dahil: kismi calismada checkpoint
        # orijinal konumunda kalir.
        counts["ERROR"] += 1

        set_checkpoint(
            original_checkpoint,
            status="error",
            records_processed=(
                counts["NEW_CLASSIFIED"]
                + counts["CHANGED"]
                + counts["UNCHANGED"]
            ),
            records_new=counts["NEW_CLASSIFIED"],
            records_changed=counts["CHANGED"],
            records_unchanged=counts["UNCHANGED"],
            records_error=counts["ERROR"],
            error_message=str(exc),
        )

        print(
            f"SYNC DURDU: {exc}",
            flush=True,
        )
        print(
            "Checkpoint ilerletilmedi.",
            flush=True,
        )
        raise

    # Tum tarama basariliysa en yeni kaydin
    # cursor'una ilerle.
    if newest_cursor is not None:
        final_checkpoint = Checkpoint(
            updated_at=newest_cursor[0],
            record_id=newest_cursor[1],
        )
    else:
        final_checkpoint = original_checkpoint

    set_checkpoint(
        final_checkpoint,
        status="idle",
        records_processed=(
            counts["NEW_CLASSIFIED"]
            + counts["CHANGED"]
            + counts["UNCHANGED"]
        ),
        records_new=counts["NEW_CLASSIFIED"],
        records_changed=counts["CHANGED"],
        records_unchanged=counts["UNCHANGED"],
        records_error=0,
        error_message=None,
    )

    print()
    print("=" * 72)
    print("INCREMENTAL AFFAIR SYNC SONUCU")
    print("=" * 72)
    print("API sayfalari:", pages)
    print("Taranan:", scanned)
    print(
        "Islenen:",
        counts["NEW_CLASSIFIED"]
        + counts["CHANGED"]
        + counts["UNCHANGED"],
    )
    print("NEW + CLASSIFIED:", counts["NEW_CLASSIFIED"])
    print("CHANGED:", counts["CHANGED"])
    print("UNCHANGED:", counts["UNCHANGED"])
    print("ERROR:", counts["ERROR"])
    print(
        "Yeni checkpoint:",
        final_checkpoint.updated_at,
        final_checkpoint.record_id,
    )


if __name__ == "__main__":
    run_incremental_sync()
