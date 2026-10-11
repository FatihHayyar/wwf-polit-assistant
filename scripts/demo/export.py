"""Export public demo data only; the source transaction is read-only."""
import gzip
import json
from pathlib import Path

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, text

import app.models  # register metadata
from app.db.database import Base, engine

DATASETS = ('affairs', 'agendas', 'meetings', 'votings', 'events',
            'documents', 'texts', 'groups', 'interests')
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
            records = db.execute(select(table).order_by(pk.desc()).limit(500)).mappings().all()
            if len(records) != 500:
                raise RuntimeError(f'{name}: fewer than 500 source records')
            rows[name] = {r[pk.name]: dict(r) for r in records}
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
                records = db.execute(select(table).where(pk.in_(ids))).mappings().all()
                target = rows.setdefault(name, {})
                for record in records:
                    target[record[pk.name]] = dict(record)
                    added += 1
            if not added:
                break
        for name in ('classification_categories', 'classification_rules',
                     'affair_classifications', 'entity_classifications'):
            table = tables[name]
            stmt = select(table)
            if name == 'affair_classifications':
                stmt = stmt.where(table.c.affair_id.in_(rows['affairs']))
            elif name == 'entity_classifications':
                from sqlalchemy import or_, and_
                stmt = stmt.where(or_(*(and_(table.c.dataset == dataset,
                                      table.c.entity_id.in_(rows[dataset])) for dataset in DATASETS)))
            keys = list(table.primary_key.columns)
            rows[name] = {tuple(r[c.name] for c in keys): dict(r) for r in db.execute(stmt).mappings()}
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
