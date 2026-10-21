from __future__ import annotations

import hashlib

import json

from dataclasses import dataclass

from datetime import datetime, timezone

from typing import Any

from app.services.change_event_service import create_change_event
from app.services.reclassification_service import reclassify_affairs



from app.classification.classifier import AffairClassifier

from app.db.database import SessionLocal

from app.models.entities import Affair

from scripts.classify_affairs import (

    classify_batch,

    load_fallback_category,

    persist_batch,

)

API_URL = "https://api.openparldata.ch/v1/affairs/"


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


def classify_new_affair(db, affair: Affair, classifier: AffairClassifier | None = None) -> None:
    classification_rows, accepted_matches, _stats, _text_count = classify_batch(
        db,
        classifier=classifier or AffairClassifier(db),
        affairs=[affair],
        fallback_category=load_fallback_category(db),
    )
    if not classification_rows:
        raise RuntimeError(f"Affair {affair.id}: classification missing")
    persist_batch(db, classification_rows=classification_rows, accepted_matches=accepted_matches)


def sync_one_affair(record: dict, db=None, classifier: AffairClassifier | None = None) -> SyncResult:
    """Insert or update one affair from an API record.

    With ``db`` the caller owns the transaction (batch mode); otherwise the
    record is written and committed in its own session.
    """
    if db is None:
        with SessionLocal() as session:
            try:
                result = _sync_affair(session, record, classifier)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise
    return _sync_affair(db, record, classifier)


def _sync_affair(db, record: dict, classifier: AffairClassifier | None) -> SyncResult:
    from fastapi.encoders import jsonable_encoder

    from app.services.sync_normalization import normalize_values

    values = normalize_values(Affair, map_affair(record))
    new_fingerprint = calculate_fingerprint(values)
    affair = db.get(Affair, values["id"])

    if affair is None:
        affair = Affair(**values)
        affair.sync_fingerprint = new_fingerprint
        db.add(affair)
        db.flush()
        classify_new_affair(db, affair, classifier)
        create_change_event(
            db,
            affair_id=affair.id,
            change_type="created",
            fingerprint=new_fingerprint,
            description="New affair detected.",
        )
        db.flush()
        return SyncResult(status="NEW_CLASSIFIED", changed_fields=[])

    changed_fields = [
        field for field, value in values.items()
        if field not in ("id", "created_at", "updated_at") and getattr(affair, field) != value
    ]
    if changed_fields:
        changes = {
            field: jsonable_encoder({"before": getattr(affair, field), "after": values[field]})
            for field in changed_fields
        }
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
        db.flush()
        return SyncResult(status="CHANGED", changed_fields=changed_fields)

    # Timestamp-only differences are stored silently.
    if affair.sync_fingerprint != new_fingerprint:
        affair.sync_fingerprint = new_fingerprint
    if "updated_at" in values and affair.updated_at != values["updated_at"]:
        affair.updated_at = values["updated_at"]
    return SyncResult(status="UNCHANGED", changed_fields=[])


def run_incremental_sync(recheck: bool = False) -> None:
    from scripts.sync.entity_sync import run_dataset
    run_dataset("affairs", recheck=recheck)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Synchronise OpenParlData affairs.")
    parser.add_argument("--recheck", action="store_true", help="Compare every affair record instead of an incremental run.")
    run_incremental_sync(recheck=parser.parse_args().recheck)
