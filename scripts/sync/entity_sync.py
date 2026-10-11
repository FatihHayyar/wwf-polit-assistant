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
from app.services.sync_normalization import normalize_values

from app.db.database import SessionLocal
from app.services.change_event_service import create_change_event
from app.services.entity_registry import ENTITIES
from app.services.entity_relations import related_affair_ids
from app.services.reclassification_service import reclassify_affairs
from app.services.entity_classification_service import classify_entity
from app.classification.classifier import AffairClassifier
from app.models.entity_classification import EntityClassification
from scripts.sync.source_batches import make_source


ADAPTERS = {
    "affairs": ("incremental_sync", "map_affair", "updated_at"),
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
    values = normalize_values(model, values)
    new = existing is None
    before_ids = set()
    changed_fields = []
    changes = {}
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
                if field not in IGNORED:
                    from fastapi.encoders import jsonable_encoder
                    changes[field] = jsonable_encoder({"before": getattr(entity, field), "after": value})
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
        changes=changes if not new else None,
        fingerprint=fingerprint(entity),
        description="New record detected." if new else "Changed fields: " + ", ".join(changed_fields),
    )
    return "NEW" if new else "CHANGED"


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
    started = time.monotonic()
    source = None
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
            source = make_source(client, adapter.API_URL, dataset, full_scan)
            if source.state and source.mode == "inventory":
                def restore_cursor(value):
                    return adapter.parse_datetime(value[0]) or datetime.min, int(value[1])
                original = restore_cursor(source.state["original"])
                newest = restore_cursor(source.state["newest"])
                upper = restore_cursor(source.state["upper"]) if source.state.get("upper") else None
                counts = dict(source.state["counts"])
                counts["ERROR"] = 0
                print(f"{dataset}: RESUME inventory position={source.position}", flush=True)
            while True:
                records, finished = source.next(sort_by)
                if not records and finished:
                    break
                if upper is None and records:
                    upper = cursor(records[0])
                selected = []
                raw_by_id = {int(record["id"]): record for record in records}
                reached = False
                for record in records:
                    position = cursor(record)
                    if not full_scan and position > upper:
                        continue
                    if not full_scan and position <= original:
                        if source.mode == "api":
                            reached = True
                            break
                        continue
                    selected.append((position, normalize_values(model, mapper(record))))
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
                        if dataset == "affairs":
                            # Preserve Affairs' existing classification/event behavior.
                            result = adapter.sync_one_affair(raw_by_id[values["id"]])
                            if result.status == "ERROR":
                                raise RuntimeError("Affair sync failed")
                            batch_counts["NEW" if result.status == "NEW_CLASSIFIED" else result.status] += 1
                            newest = max(newest, position)
                            continue
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
                state = dict(counts=counts, original=[original[0].isoformat(), original[1]],
                             newest=[newest[0].isoformat(), newest[1]],
                             upper=[upper[0].isoformat(), upper[1]] if upper else None, complete=False)
                source.commit(state)
                save("running")
                print(f"{dataset}: mode={source.mode} position={source.position} {counts}", flush=True)
                if reached or finished:
                    break
        save("idle", final=newest)
        if source is not None:
            source.commit(dict(counts=counts, original=[original[0].isoformat(), original[1]],
                               newest=[newest[0].isoformat(), newest[1]], upper=None, complete=True))
    except BaseException as exc:
        counts["ERROR"] += 1
        save("error", str(exc))
        raise
    finally:
        print("\n" + "=" * 72, flush=True)
        print(f"{dataset.upper()} SYNC SONUCU", flush=True)
        print("=" * 72, flush=True)
        print(f"API sayfalari: {source.api_calls if source else 0}", flush=True)
        print(f"Taranan (bu deneme): {source.scanned if source else 0}", flush=True)
        print(f"Islenen: {sum(counts[k] for k in ('NEW','CHANGED','UNCHANGED'))}", flush=True)
        for key in ("NEW", "CHANGED", "UNCHANGED", "ERROR"):
            print(f"{key}: {counts[key]}", flush=True)
        print(f"Checkpoint: {'ilerletilmedi' if counts['ERROR'] else newest}", flush=True)
        print(f"Sure: {time.monotonic()-started:.1f} seconds", flush=True)
