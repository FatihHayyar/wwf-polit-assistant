"""Build deferred large unified-search indexes without rerunning migrations.

Run explicitly in a maintenance window. Public dataset search does not require
these experimental indexes. This command never starts a data sync or SMTP send.
"""
import importlib.util
from pathlib import Path
from sqlalchemy import text
from app.db.database import engine


def main():
    path = Path(__file__).resolve().parents[1] / "migrations/versions/20261011_unified_search.py"
    spec = importlib.util.spec_from_file_location("unified_search_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as db:
        for statement in module.STATEMENTS:
            name = statement.split()[5]
            if name not in {"idx_documents_content_search", "idx_texts_content_search"}:
                continue
            valid = db.scalar(text("SELECT indisvalid FROM pg_index WHERE indexrelid=to_regclass(:name)"), {"name": name})
            if valid:
                print(f"{name}: already valid", flush=True)
                continue
            if valid is False:
                db.execute(text(f'DROP INDEX CONCURRENTLY IF EXISTS "{name}"'))
            statement = statement.replace('USING gin ((lower(', "USING gin ((to_tsvector('simple'::regconfig, left(lower(")
            statement = statement.replace(')) gin_trgm_ops)', '), 100000))) )')
            print(f"Building {name}; large mirrors may take substantial time.", flush=True)
            db.execute(text(statement.replace("CREATE INDEX IF NOT EXISTS", "CREATE INDEX CONCURRENTLY IF NOT EXISTS")))
            print(f"{name}: complete", flush=True)


if __name__ == "__main__":
    main()
