from __future__ import annotations

import hashlib

import json
import time

from dataclasses import dataclass

from datetime import datetime, timezone

from typing import Any

from app.services.change_event_service import create_change_event
from app.services.reclassification_service import reclassify_affairs

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
MAX_REQUEST_ATTEMPTS = 5
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

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
        db.execute(text("INSERT INTO sync_checkpoints (dataset, status) VALUES ('affairs', 'idle') ON CONFLICT (dataset) DO NOTHING"))
        db.commit()
        row = db.execute(text("SELECT last_updated_at, last_id FROM sync_checkpoints WHERE dataset = 'affairs'")).first()
    if row is None:
        raise RuntimeError("Affairs checkpoint could not be created")
    return Checkpoint(updated_at=parse_datetime(row[0]), record_id=row[1])

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

    from app.services.sync_normalization import normalize_values
    values = normalize_values(Affair, map_affair(record))

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
            changes = {}

            for field, value in values.items():

                if field in (

                    "id",

                    "created_at",

                    "updated_at",

                ):

                    continue

                if getattr(affair, field) != value:

                    changed_fields.append(field)
                    from fastapi.encoders import jsonable_encoder
                    changes[field] = jsonable_encoder({"before": getattr(affair, field), "after": value})

            if changed_fields:

                for field in changed_fields:

                    setattr(affair, field, values[field])

                if "updated_at" in values:

                    affair.updated_at = values["updated_at"]

                affair.sync_fingerprint = new_fingerprint

                if any(field.startswith(("title_", "title_long_")) for field in changed_fields):
                    reclassify_affairs(db, {affair.id})

                create_change_event(

                     db,

                     affair_id=affair.id,

                     change_type="updated",
                     changes=changes,
                     new_occurrence=True,

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
    params = {
        "limit": PAGE_SIZE,
        "offset": offset,
        "sort_by": "-updated_at,-id",
    }

    for attempt in range(1, MAX_REQUEST_ATTEMPTS + 1):
        try:
            response = client.get(API_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            records = payload.get("data")
            if not isinstance(records, list):
                raise RuntimeError("API response: data listesi bulunamadi.")
            return records
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in RETRYABLE_STATUS_CODES:
                raise
            error = exc
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            error = exc

        if attempt == MAX_REQUEST_ATTEMPTS:
            print(
                f"API istegi basarisiz: offset={offset}, "
                f"{MAX_REQUEST_ATTEMPTS} deneme yapildi. Son hata: {error}",
                flush=True,
            )
            raise error

        wait_seconds = min(2 ** (attempt - 1), 16)
        print(
            f"API gecici hata: offset={offset}, deneme={attempt}/{MAX_REQUEST_ATTEMPTS}, "
            f"hata={type(error).__name__}: {error}. "
            f"{wait_seconds} saniye sonra tekrar denenecek.",
            flush=True,
        )
        time.sleep(wait_seconds)

    raise RuntimeError("Unexpected retry loop exit")

def run_incremental_sync() -> None:
    from scripts.sync.entity_sync import run_dataset
    run_dataset("affairs")


if __name__ == "__main__":
    run_incremental_sync()
