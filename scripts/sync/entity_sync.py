"""Shared, batched sync for all nine datasets.

A regular run of one dataset consists of up to three phases:

1. **Incremental** – read the source sorted by ``-updated_at`` (records without
   a timestamp excluded) until the stored checkpoint is reached. Agendas have no
   modification timestamp; they re-check a window around ``item_date`` instead.
2. **New identities** – read the source sorted by ``-id`` until the highest
   local ID. This finds new records whose timestamp is missing or older than the
   checkpoint.
3. **Missing identities** – only if the source still has more records than the
   local table: hydrate exactly the absent IDs from the bulk inventory.

A **full scan** compares every record. It runs when requested (``--recheck``),
when a dataset has never been fully scanned, or when its configured interval has
passed. This catches changes the source made without updating ``updated_at``.

Timestamp-only updates never produce change events. Checkpoints advance only
after a successful run; committed batches can safely be replayed on failure.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta
from importlib import import_module

import httpx
from sqlalchemy import func, select, text
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


# dataset: (adapter module, mapper, source modification timestamp or None)
ADAPTERS = {
    "affairs": ("incremental_sync", "map_affair", "updated_at"),
    "agendas": ("agendas_sync", "map_agenda", None),
    "meetings": ("meetings_sync", "map_meeting", "updated_at"),
    "votings": ("votings_sync", "map_voting", "updated_at"),
    "events": ("events_sync", "map_event", "updated_at"),
    "documents": ("docs_sync", "map_document", "updated_at"),
    "texts": ("texts_sync", "map_text", "updated_at"),
    "groups": ("groups_sync", "map_group", "updated_at"),
    "interests": ("interests_sync", "map_interest", "updated_at"),
}

# Days between complete comparisons. Shorter where the source leaves
# updated_at empty for many records (events, votings) or has none (agendas).
# Documents carry full texts; they are fully compared only on request.
FULL_SCAN_DAYS = {
    "affairs": 30, "agendas": 7, "meetings": 30, "votings": 7, "events": 7,
    "documents": None, "texts": 14, "groups": 7, "interests": 7,
}

# Agendas: records whose item_date lies within this many days of today are
# re-checked daily, so status and results of current sessions stay fresh.
WINDOWS = {"agendas": ("item_date", 60)}

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


def full_scan_due(dataset, last_full_scan_at, now=None):
    interval = FULL_SCAN_DAYS[dataset]
    if interval is None:
        return False
    if last_full_scan_at is None:
        return True
    return (now or datetime.now()) - last_full_scan_at >= timedelta(days=interval)


def run_dataset(dataset, recheck=False, backfill_missing_classifications=True, now=None):
    module_name, mapper_name, cursor_field = ADAPTERS[dataset]
    adapter = import_module(f"scripts.sync.{module_name}")
    mapper = getattr(adapter, mapper_name)
    model = ENTITIES[dataset].model
    key = "source_id" if dataset == "documents" else "id"
    source_key = getattr(model, key)
    checkpoint_key = "docs" if dataset == "documents" else dataset
    with SessionLocal() as db:
        db.execute(text("INSERT INTO sync_checkpoints (dataset, status) VALUES (:dataset, 'idle') ON CONFLICT (dataset) DO NOTHING"), {"dataset": checkpoint_key})
        db.commit()
        row = db.execute(text("SELECT last_updated_at, last_id, last_full_scan_at FROM sync_checkpoints WHERE dataset=:dataset"),
                         {"dataset": checkpoint_key}).first()
        start_maximum_id = db.scalar(select(func.max(source_key))) or 0
    original = (adapter.parse_datetime(row[0]) or datetime.min, int(row[1] or 0))
    full_scan = recheck or full_scan_due(dataset, adapter.parse_datetime(row[2]), now)
    progress = dict(newest=original, upper=None)
    counts = dict(NEW=0, CHANGED=0, UNCHANGED=0, ERROR=0)
    started = time.monotonic()
    sources = []

    def cursor(record):
        if not cursor_field:
            return datetime.min, int(record["id"])
        date = adapter.parse_datetime(record.get(cursor_field))
        if date is None:
            raise ValueError(f"{dataset} {record['id']}: missing {cursor_field}")
        return date, int(record["id"])

    def save(status, error=None, final=None, full_scan_completed=False):
        date, record_id = final or original
        with SessionLocal() as db:
            db.execute(text("""UPDATE sync_checkpoints SET last_updated_at=:date, last_id=:id,
                last_run_at=CURRENT_TIMESTAMP, status=:status, records_processed=:processed,
                records_new=:new, records_changed=:changed, records_unchanged=:unchanged,
                records_error=:errors, error_message=:error,
                last_full_scan_at=CASE WHEN :full THEN CURRENT_TIMESTAMP ELSE last_full_scan_at END
                WHERE dataset=:dataset"""),
                dict(dataset=checkpoint_key, date=date if cursor_field else None, id=record_id,
                     status=status, processed=sum(counts[k] for k in ("NEW", "CHANGED", "UNCHANGED")),
                     new=counts["NEW"], changed=counts["CHANGED"], unchanged=counts["UNCHANGED"],
                     errors=counts["ERROR"], error=error, full=full_scan_completed))
            db.commit()

    def apply(records, track_cursor):
        """Write one page of source records in a single transaction.

        With ``track_cursor`` the checkpoint advances to the newest source
        timestamp of the page; records without a timestamp do not move it.
        """
        selected = [(cursor(record) if track_cursor and record.get(cursor_field) else None,
                     normalize_values(model, mapper(record))) for record in records]
        raw_by_id = {int(record["id"]): record for record in records}
        ids = [values[key] for _, values in selected]
        batch_counts = dict(NEW=0, CHANGED=0, UNCHANGED=0)
        with SessionLocal() as db:
            classifier = None
            existing = {}
            if ids:
                for entity in db.scalars(select(model).where(source_key.in_(ids))):
                    existing.setdefault(getattr(entity, key), []).append(entity)
            entity_ids = [entity.pk if dataset == "documents" else entity.id
                          for candidates in existing.values() for entity in candidates]
            classified = set(db.scalars(select(EntityClassification.entity_id).where(
                EntityClassification.dataset == dataset, EntityClassification.entity_id.in_(entity_ids)))) if entity_ids else set()
            for position, values in selected:
                if dataset == "affairs":
                    # Affairs keep their own classification and event rules but
                    # share this batch's session and classifier.
                    if classifier is None and values["id"] not in existing:
                        classifier = AffairClassifier(db)
                    result = adapter.sync_one_affair(raw_by_id[values["id"]], db=db, classifier=classifier)
                    batch_counts["NEW" if result.status == "NEW_CLASSIFIED" else result.status] += 1
                else:
                    candidates = existing.get(values[key], [])
                    entity = choose_document(candidates, values) if dataset == "documents" else (candidates[0] if candidates else None)
                    missing_classification = entity is not None and (entity.pk if dataset == "documents" else entity.id) not in classified
                    if classifier is None and (entity is None or missing_classification or any(
                            field not in IGNORED and getattr(entity, field) != value for field, value in values.items())):
                        classifier = AffairClassifier(db)
                    result = sync_record(db, dataset, values, entity, classifier=classifier)
                    if result == "UNCHANGED" and missing_classification and backfill_missing_classifications:
                        classify_entity(db, dataset, entity, classifier=classifier)
                    batch_counts[result] += 1
                    if entity is None:
                        # Make repeated source identities in one API page visible.
                        db.flush()
                        existing[values[key]] = list(db.scalars(select(model).where(source_key == values[key])))
                if position is not None:
                    progress["newest"] = max(progress["newest"], position)
            db.commit()
        for name, count in batch_counts.items():
            counts[name] += count

    def state(source, full):
        upper = progress["upper"]
        return dict(counts=counts, original=[original[0].isoformat(), original[1]],
                    newest=[progress["newest"][0].isoformat(), progress["newest"][1]],
                    upper=[upper[0].isoformat(), upper[1]] if upper else None, complete=False, full_scan=full)

    def report(source, phase):
        print(f"{dataset}: phase={phase} mode={source.mode} position={source.position} {counts}", flush=True)

    def inventory_phase(source, full):
        """Hydrate an ID inventory (all IDs or only missing ones) in committed batches."""
        while True:
            records, finished = source.next("-id")
            if records:
                apply(records, track_cursor=full and cursor_field is not None)
                if full and not cursor_field:
                    for record in records:
                        progress["newest"] = max(progress["newest"], (datetime.min, int(record["id"])))
            source.commit(state(source, full))
            save("running")
            report(source, "full" if full else "missing")
            if finished:
                return

    def api_source(client):
        # API phases are cheap to repeat and keep no resume state; only
        # inventory phases persist their position.
        source = make_source(client, adapter.API_URL, dataset, False)
        source.path = None
        sources.append(source)
        return source

    def incremental_phase(client):
        source = api_source(client)
        if dataset in WINDOWS:
            field, days = WINDOWS[dataset]
            source.params = {"exclude_null": field}
            sort_by = f"-{field},-id"
            limit = (now or datetime.now()) - timedelta(days=days)
            while True:
                records, finished = source.next(sort_by)
                window = [record for record in records
                          if (adapter.parse_datetime(record.get(field)) or datetime.min) >= limit]
                if window:
                    apply(window, track_cursor=False)
                    for record in window:
                        progress["newest"] = max(progress["newest"], (datetime.min, int(record["id"])))
                source.commit(state(source, False))
                report(source, "window")
                if finished or len(window) < len(records):
                    return
        source.params = {"exclude_null": cursor_field}
        sort_by = f"-{cursor_field},-id"
        while True:
            records, finished = source.next(sort_by)
            if source.mode == "inventory":
                # The source's offset cap was reached; its ID inventory is not
                # ordered by timestamp, so every record is compared.
                if records:
                    apply(records, track_cursor=True)
                source.commit(state(source, False))
                report(source, "incremental-inventory")
                if finished:
                    return
                continue
            if progress["upper"] is None and records:
                progress["upper"] = cursor(records[0])
            selected = []
            reached = False
            for record in records:
                position = cursor(record)
                if position > progress["upper"]:
                    continue  # Changed during this run; the next run picks it up.
                if position <= original:
                    reached = True
                    break
                selected.append(record)
            if selected:
                apply(selected, track_cursor=True)
            source.commit(state(source, False))
            report(source, "incremental")
            if reached or finished:
                return

    def new_identity_phase(client):
        source = api_source(client)
        previous_minimum = None
        while True:
            records, finished = source.next("-id")
            if records and getattr(source, "maximum_id", None) is None:
                source.maximum_id = int(records[0]["id"])
            fresh = [record for record in records if int(record["id"]) > start_maximum_id]
            if fresh:
                apply(fresh, track_cursor=False)
                if not cursor_field:
                    for record in fresh:
                        progress["newest"] = max(progress["newest"], (datetime.min, int(record["id"])))
            source.commit(state(source, False))
            report(source, "new-ids")
            minimum = min((int(record["id"]) for record in records), default=None)
            stalled = minimum is not None and previous_minimum is not None and minimum >= previous_minimum
            if finished or len(fresh) < len(records) or stalled:
                return source
            previous_minimum = minimum

    def missing_identity_phase(client, head_source):
        """Hydrate only IDs that the source has and the local table lacks."""
        total = getattr(head_source, "total_records", None)
        if not isinstance(total, int):
            return
        with SessionLocal() as db:
            # Docs metadata counts relationship variants as rows,
            # so compare row counts rather than distinct source IDs.
            count_expression = func.count() if dataset == "documents" else func.count(func.distinct(source_key))
            local_count = db.execute(select(count_expression).select_from(model)).scalar()
            if local_count >= total:
                return
            existing_ids = set(db.scalars(select(source_key).distinct()))
        print(f"{dataset}: source has {total} records, local has {local_count}; checking missing identities", flush=True)
        source = make_source(client, adapter.API_URL, dataset, True)
        source.mode, source.position, source.next_position, source.state = "inventory", 0, 0, {}
        sources.append(source)
        if dataset == "texts":
            # The texts API ignores ID filters; its inventory is grouped by affair.
            inventory_phase(source, True)
            return True
        maximum_id = getattr(head_source, "maximum_id", None)
        if dataset == "documents" and maximum_id and 0 < maximum_id <= total * 2:
            # Dense positive IDs let us probe every absent identity with ID
            # filters instead of downloading multi-gigabyte exports.
            source.reconciliation_ids = sorted(set(range(1, maximum_id + 1)) - existing_ids, reverse=True)
        else:
            source.inventory()
            source.reconciliation_ids = [record_id for record_id in source.ids if record_id not in existing_ids]
        source.ids = list(source.reconciliation_ids)
        print(f"{dataset}: {len(source.ids)} missing identity candidates", flush=True)
        # Persist the candidate list first, so a resumed job need not rebuild it.
        source.commit(state(source, False))
        inventory_phase(source, False)
        return False

    save("running")
    full_scan_completed = False
    try:
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            resumed = make_source(client, adapter.API_URL, dataset, True)
            if resumed.state and resumed.mode == "inventory" and not resumed.state.get("complete"):
                # Continue an interrupted inventory phase of the same job.
                sources.append(resumed)
                original = (adapter.parse_datetime(resumed.state["original"][0]) or datetime.min, int(resumed.state["original"][1]))
                progress["newest"] = (adapter.parse_datetime(resumed.state["newest"][0]) or datetime.min, int(resumed.state["newest"][1]))
                counts = dict(resumed.state["counts"])
                counts["ERROR"] = 0
                full_scan = resumed.state.get("full_scan", full_scan)
                print(f"{dataset}: RESUME inventory position={resumed.position}", flush=True)
                inventory_phase(resumed, full_scan)
                full_scan_completed = full_scan
            elif full_scan:
                print(f"{dataset}: full comparison of every record", flush=True)
                sources.append(resumed)
                inventory_phase(resumed, True)
                full_scan_completed = True
            else:
                incremental_phase(client)
                head = new_identity_phase(client)
                full_scan_completed = bool(missing_identity_phase(client, head))
        save("idle", final=progress["newest"], full_scan_completed=full_scan_completed)
        for source in sources:
            source.commit(dict(state(source, full_scan_completed), complete=True))
    except BaseException as exc:
        counts["ERROR"] += 1
        save("error", str(exc))
        raise
    finally:
        print("\n" + "=" * 72, flush=True)
        print(f"{dataset.upper()} SYNC RESULT", flush=True)
        print("=" * 72, flush=True)
        print(f"API requests: {sum(source.api_calls for source in sources)}", flush=True)
        print(f"Records read: {sum(source.scanned for source in sources)}", flush=True)
        print(f"Processed: {sum(counts[k] for k in ('NEW', 'CHANGED', 'UNCHANGED'))}", flush=True)
        for name in ("NEW", "CHANGED", "UNCHANGED", "ERROR"):
            print(f"{name}: {counts[name]}", flush=True)
        print(f"Full comparison: {'yes' if full_scan_completed else 'no'}", flush=True)
        print(f"Checkpoint: {'not advanced' if counts['ERROR'] else progress['newest']}", flush=True)
        print(f"Duration: {time.monotonic() - started:.1f} seconds", flush=True)
