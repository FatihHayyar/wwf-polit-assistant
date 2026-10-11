"""Shared, batched sync for related datasets.

Datasets without a reliable modification cursor are fully checked. Their
timestamp-only updates never produce change events. Checkpoints advance only
after the complete run; committed batches can safely be replayed on failure.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from importlib import import_module

import httpx
from sqlalchemy import select, text

from app.db.database import SessionLocal
from app.services.change_event_service import create_change_event
from app.services.entity_registry import ENTITIES
from app.services.entity_relations import related_affair_ids
from app.services.reclassification_service import reclassify_affairs
from app.services.entity_classification_service import classify_entity
from app.classification.classifier import AffairClassifier
from app.models.entity_classification import EntityClassification


ADAPTERS = {
    "agendas": ("agendas_sync", "map_agenda", None),
    "meetings": ("meetings_sync", "map_meeting", "updated_at"),
    "votings": ("votings_sync", "map_voting", None),
    "events": ("events_sync", "map_event", None),
    "documents": ("docs_sync", "map_document", "updated_at"),
    "texts": ("texts_sync", "map_text", None),
    "groups": ("groups_sync", "map_group", None),
    "interests": ("interests_sync", "map_interest", None),
}
IGNORED = {"id", "pk", "source_id", "created_at", "updated_at", "sync_fingerprint"}
PAGE_SIZE = 500


def fingerprint(entity) -> str:
    payload = {column.key: getattr(entity, column.key) for column in entity.__table__.columns
               if column.key not in IGNORED}
    value = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def choose_document(candidates, values):
    identity = ("body_id", "affair_id", "agenda_id", "meeting_id", "language", "parent_type")
    matching = [row for row in candidates if all(
        getattr(row, field) == values[field] for field in identity if field in values
    )]
    if len(matching) > 1:
        raise ValueError(f"Ambiguous document identity for source_id={values['source_id']}")
    return matching[0] if matching else None


def sync_record(db, dataset, values, existing=None, classifier=None):
    model = ENTITIES[dataset].model
    new = existing is None
    before_ids = set()
    changed_fields = []
    if new:
        entity = model(**values)
        db.add(entity)
    else:
        entity = existing
        meaningful_change = any(field not in IGNORED and getattr(entity, field) != value
                                for field, value in values.items())
        if meaningful_change:
            before_ids = related_affair_ids(db, dataset, existing)
        for field, value in values.items():
            if field in {"id", "pk", "source_id", "created_at"}:
                continue
            if getattr(entity, field) != value:
                setattr(entity, field, value)
                if field not in IGNORED:
                    changed_fields.append(field)
    if not new and not changed_fields:
        return "UNCHANGED"
    db.flush()
    ids = before_ids | related_affair_ids(db, dataset, entity)
    classify_entity(db, dataset, entity, classifier=classifier)
    if dataset == "texts":
        reclassify_affairs(db, ids)
    create_change_event(
        db, dataset=dataset,
        source_id=entity.pk if dataset == "documents" else entity.id,
        affair_id=min(ids) if ids else None, affair_ids=ids,
        change_type="created" if new else "updated",
        new_occurrence=not new,
        fingerprint=fingerprint(entity),
        description="New record detected." if new else "Changed fields: " + ", ".join(changed_fields),
    )
    return "NEW" if new else "CHANGED"


def fetch_page(client, url, offset, sort_by):
    for attempt in range(5):
        try:
            response = client.get(url, params={"limit": PAGE_SIZE, "offset": offset, "sort_by": sort_by})
            response.raise_for_status()
            records = response.json().get("data")
            if not isinstance(records, list):
                raise ValueError("API response must contain a data list")
            return records
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in {429, 500, 502, 503, 504} or attempt == 4:
                raise
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError):
            if attempt == 4:
                raise
        time.sleep(min(2 ** attempt, 16))
    raise RuntimeError("Retry loop exhausted")


def run_dataset(dataset, recheck=False):
    module_name, mapper_name, cursor_field = ADAPTERS[dataset]
    adapter = import_module(f"scripts.sync.{module_name}")
    mapper = getattr(adapter, mapper_name)
    model = ENTITIES[dataset].model
    checkpoint_key = "docs" if dataset == "documents" else dataset
    with SessionLocal() as db:
        db.execute(text("INSERT INTO sync_checkpoints (dataset, status) VALUES (:dataset, 'idle') ON CONFLICT (dataset) DO NOTHING"), {"dataset": checkpoint_key})
        db.commit()
        row = db.execute(text("SELECT last_updated_at, last_id FROM sync_checkpoints WHERE dataset=:dataset"), {"dataset": checkpoint_key}).first()
    original = (adapter.parse_datetime(row[0]) or datetime.min, int(row[1] or 0))
    newest = original
    upper = None
    counts = dict(NEW=0, CHANGED=0, UNCHANGED=0, ERROR=0)
    offset = 0
    full_scan = recheck or cursor_field is None
    sort_by = f"-{cursor_field},-id" if cursor_field else "-id"

    def cursor(record):
        if not cursor_field:
            return datetime.min, int(record["id"])
        date = adapter.parse_datetime(record.get(cursor_field))
        if date is None:
            raise ValueError(f"{dataset} {record['id']}: missing {cursor_field}")
        return date, int(record["id"])

    def save(status, error=None, final=None):
        date, record_id = final or original
        with SessionLocal() as db:
            db.execute(text("""UPDATE sync_checkpoints SET last_updated_at=:date, last_id=:id,
                last_run_at=CURRENT_TIMESTAMP, status=:status, records_processed=:processed,
                records_new=:new, records_changed=:changed, records_unchanged=:unchanged,
                records_error=:errors, error_message=:error WHERE dataset=:dataset"""),
                dict(dataset=checkpoint_key, date=date if cursor_field else None, id=record_id,
                     status=status, processed=sum(counts[k] for k in ("NEW", "CHANGED", "UNCHANGED")),
                     new=counts["NEW"], changed=counts["CHANGED"], unchanged=counts["UNCHANGED"],
                     errors=counts["ERROR"], error=error))
            db.commit()

    save("running")
    try:
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            while True:
                records = fetch_page(client, adapter.API_URL, offset, sort_by)
                if not records:
                    break
                if upper is None:
                    upper = cursor(records[0])
                selected = []
                reached = False
                for record in records:
                    position = cursor(record)
                    if position > upper:
                        continue
                    if not full_scan and position <= original:
                        reached = True
                        break
                    selected.append((position, mapper(record)))
                key = "source_id" if dataset == "documents" else "id"
                ids = [values[key] for _, values in selected]
                with SessionLocal() as db:
                    classifier = None
                    existing = {}
                    if ids:
                        for entity in db.scalars(select(model).where(getattr(model, key).in_(ids))):
                            existing.setdefault(getattr(entity, key), []).append(entity)
                    entity_ids = [entity.pk if dataset == "documents" else entity.id
                                  for candidates in existing.values() for entity in candidates]
                    classified = set(db.scalars(select(EntityClassification.entity_id).where(
                        EntityClassification.dataset == dataset, EntityClassification.entity_id.in_(entity_ids)))) if entity_ids else set()
                    batch_counts = dict(NEW=0, CHANGED=0, UNCHANGED=0)
                    for position, values in selected:
                        candidates = existing.get(values[key], [])
                        entity = choose_document(candidates, values) if dataset == "documents" else (candidates[0] if candidates else None)
                        missing_classification = entity is not None and (entity.pk if dataset == "documents" else entity.id) not in classified
                        if entity is None or any(field not in IGNORED and getattr(entity, field) != value for field, value in values.items()):
                            if classifier is None:
                                classifier = AffairClassifier(db)
                        result = sync_record(db, dataset, values, entity, classifier=classifier)
                        if result == "UNCHANGED" and missing_classification:
                            if classifier is None:
                                classifier = AffairClassifier(db)
                            classify_entity(db, dataset, entity, classifier=classifier)
                        batch_counts[result] += 1
                        if entity is None:
                            # Make repeated source identities in one API page visible.
                            db.flush()
                            existing[values[key]] = list(db.scalars(select(model).where(getattr(model, key) == values[key])))
                        newest = max(newest, position)
                    db.commit()
                for name, count in batch_counts.items():
                    counts[name] += count
                print(f"{dataset}: offset={offset} {counts}", flush=True)
                if reached or len(records) < PAGE_SIZE:
                    break
                offset += PAGE_SIZE
        save("idle", final=newest)
    except BaseException as exc:
        counts["ERROR"] += 1
        save("error", str(exc))
        raise
