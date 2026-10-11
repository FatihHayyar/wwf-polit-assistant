"""Migrate and seed a separate demo database, then serve the application."""
import gzip
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, select, text
import uvicorn

import app.models
from app.db.database import Base, engine
from scripts.demo.export import DATASETS


def seed():
    tables = Base.metadata.tables
    with engine.begin() as db:
        # Startup is atomic, including the empty-database check.
        db.execute(text('SELECT pg_advisory_xact_lock(20261011500)'))
        if any(db.execute(select(tables[name]).limit(1)).first() for name in DATASETS):
            print('Existing demo data retained; bootstrap skipped.')
            return
        with gzip.open(Path('data/demo/sample.json.gz'), 'rt', encoding='utf-8') as source:
            payload = json.load(source)['tables']
        for table in Base.metadata.sorted_tables:
            records = payload.get(table.name, [])
            for row in records:
                for column in table.columns:
                    if isinstance(column.type, DateTime) and row.get(column.name):
                        row[column.name] = datetime.fromisoformat(row[column.name])
            if records:
                db.execute(table.insert(), records)
                if len(table.primary_key.columns) != 1:
                    continue
                pk = next(iter(table.primary_key.columns))
                db.execute(text("SELECT setval(pg_get_serial_sequence(:table, :pk), "
                                "GREATEST(:maximum, 1), true) "
                                "WHERE pg_get_serial_sequence(:table, :pk) IS NOT NULL"),
                           {'table': table.name, 'pk': pk.name,
                            'maximum': max(r[pk.name] for r in records)})
        print('Demo data loaded successfully.')


if __name__ == '__main__':
    subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], check=True)
    seed()
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000)
