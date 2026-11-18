"""Export public demo data only; the source transaction is read-only."""
import gzip
import json
from datetime import date, timedelta
from pathlib import Path

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, exists, func, select, text

import app.models  # noqa: F401  (registers all tables on Base.metadata)
from app.db.database import Base, engine
from app.services.demo_notification_service import DEMO_ID_START

DATASETS = ('affairs', 'agendas', 'meetings', 'votings', 'events',
            'documents', 'texts', 'groups', 'interests')
# The demo holds the last year of parliamentary activity, selected by the
# date of the business itself. Groups and interests have no such date and
# keep their newest records; linked records follow through the references.
DAYS = 365
DATE_COLUMNS = {'affairs': 'begin_date', 'agendas': 'item_date', 'meetings': 'begin_date',
                'votings': 'date', 'events': 'date', 'documents': 'date', 'texts': 'text_date'}
NEWEST = 500
# Every dataset also gets the newest records of each subtopic, so topic
# filters in the demo are not empty.
PER_CATEGORY = 3
# Keeps the snapshot small: document texts keep only their beginning.
MAX_DOCUMENT_TEXT = 2_000
# Stays below the bind parameter limit of PostgreSQL.
CHUNK = 10_000


def columns(table):
    """Selects a table; long document texts are cut in the database."""
    if table.name != 'documents':
        return select(table)
    return select(*(func.left(c, MAX_DOCUMENT_TEXT).label(c.name) if c.name == 'text' else c
                    for c in table.columns))


def fetch(db, table, ids):
    pk = next(iter(table.primary_key.columns))
    ids = list(ids)
    for start in range(0, len(ids), CHUNK):
        yield from db.execute(columns(table).where(pk.in_(ids[start:start + CHUNK]))).mappings()


def add_category_examples(db, tables, rows):
    categories = tables['classification_categories']
    child = categories.alias('child')
    leaves = db.scalars(select(categories.c.id).where(
        ~exists().where(child.c.parent_id == categories.c.id))).all()
    for name in DATASETS:
        table = tables[name]
        pk = next(iter(table.primary_key.columns))
        if name == 'affairs':
            classification = tables['affair_classifications']
            reference, scope = classification.c.affair_id, []
        else:
            classification = tables['entity_classifications']
            reference, scope = classification.c.entity_id, [classification.c.dataset == name]
        for category_id in leaves:
            ids = (select(reference).where(classification.c.category_id == category_id, *scope)
                   .order_by(reference.desc()).limit(PER_CATEGORY))
            if name == 'affairs':
                ids = ids.where(reference < DEMO_ID_START)
            for record in db.execute(columns(table).where(pk.in_(ids))).mappings():
                rows[name][record[pk.name]] = dict(record)
REFERENCES = {'body_id': 'bodies', 'person_id': 'persons',
              'group_id': 'groups', 'meeting_id': 'meetings',
              'agenda_id': 'agendas', 'affair_id': 'affairs',
              'item_affair_id': 'affairs'}


def main():
    tables = Base.metadata.tables
    rows = {}
    with engine.connect() as db:
        db.execute(text('SET TRANSACTION READ ONLY'))
        for name in DATASETS:
            table = tables[name]
            pk = next(iter(table.primary_key.columns))
            if name in DATE_COLUMNS:
                since = date.today() - timedelta(days=DAYS)
                chosen = columns(table).where(table.c[DATE_COLUMNS[name]] >= since)
            else:
                chosen = columns(table).order_by(pk.desc()).limit(NEWEST)
            if name == 'affairs':
                # Never export fictitious test affairs from a live demo run.
                chosen = chosen.where(pk < DEMO_ID_START)
            records = db.execute(chosen).mappings().all()
            if len(records) < NEWEST:
                raise RuntimeError(f'{name}: fewer than {NEWEST} source records')
            rows[name] = {r[pk.name]: dict(r) for r in records}
        add_category_examples(db, tables, rows)
        # Preserve forward links without fabricating or deleting source relationships.
        while True:
            needed = {}
            for records in list(rows.values()):
                for row in records.values():
                    for field, target in REFERENCES.items():
                        value = row.get(field)
                        if value is not None and value not in rows.get(target, {}):
                            needed.setdefault(target, set()).add(value)
            added = 0
            for name, ids in needed.items():
                table = tables[name]
                pk = next(iter(table.primary_key.columns))
                target = rows.setdefault(name, {})
                for record in fetch(db, table, ids):
                    target[record[pk.name]] = dict(record)
                    added += 1
            if not added:
                break
        for name in ('classification_categories', 'classification_rules',
                     'affair_classifications', 'entity_classifications'):
            table = tables[name]
            keys = list(table.primary_key.columns)
            if name == 'affair_classifications':
                scopes = [(table.c.affair_id, [], list(rows['affairs']))]
            elif name == 'entity_classifications':
                scopes = [(table.c.entity_id, [table.c.dataset == dataset], list(rows[dataset]))
                          for dataset in DATASETS]
            else:
                scopes = [(None, [], [None])]
            rows[name] = {}
            for column, condition, ids in scopes:
                for start in range(0, len(ids), CHUNK):
                    stmt = select(table)
                    if column is not None:
                        stmt = stmt.where(and_(*condition, column.in_(ids[start:start + CHUNK])))
                    for r in db.execute(stmt).mappings():
                        rows[name][tuple(r[c.name] for c in keys)] = dict(r)
    for row in rows.get('persons', {}).values():
        row['email'] = None
    payload = {'source': 'OpenParlData.ch / CC BY 4.0',
               'tables': {name: list(records.values()) for name, records in rows.items()}}
    destination = Path('data/demo/sample.json.gz')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(destination, 'wt', encoding='utf-8') as output:
        json.dump(jsonable_encoder(payload), output, ensure_ascii=False)
    print({name: len(records) for name, records in rows.items()})
    print(f'Demo snapshot: {destination.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
