"""Read-only live source comparison against local cursors and recent records."""
import json
from importlib import import_module
from pathlib import Path

import httpx
from sqlalchemy import func, select, text

from app.db.database import SessionLocal
from app.services.entity_registry import ENTITIES
from app.services.sync_normalization import normalize_values
from scripts.sync.entity_sync import ADAPTERS, IGNORED
from scripts.sync.source_batches import request


def main():
    report = {}
    with httpx.Client(timeout=60, follow_redirects=True) as client, SessionLocal() as db:
        for dataset, (module, mapper_name, cursor_field) in ADAPTERS.items():
            adapter = import_module("scripts.sync." + module)
            model = ENTITIES[dataset].model
            key = "source_id" if dataset == "documents" else "id"
            sort = f"-{cursor_field},-id" if cursor_field else "-id"
            data = request(client, adapter.API_URL, params={"limit": 500, "offset": 0, "sort_by": sort}).json()
            rows = data["data"]
            checkpoint = db.execute(text("SELECT last_updated_at,last_id FROM sync_checkpoints WHERE dataset=:dataset"),
                                    {"dataset": "docs" if dataset == "documents" else dataset}).first()
            detail = {"source_meta": data.get("meta"), "sample_size": len(rows),
                      "local_count": db.scalar(select(func.count()).select_from(model)),
                      "local_identity_count": db.scalar(select(func.count(func.distinct(getattr(model, key))))),
                      "checkpoint": list(checkpoint), "latest_source": {k: rows[0].get(k) for k in ["id", "created_at", "updated_at"]} if rows else None,
                      "newer_than_cursor": [], "missing": [], "changed": [], "mapping_errors": []}
            for record in rows:
                if cursor_field and (adapter.parse_datetime(record.get(cursor_field)), int(record["id"])) > (adapter.parse_datetime(checkpoint[0]), int(checkpoint[1])):
                    detail["newer_than_cursor"].append(record["id"])
            if dataset == "events" and rows:
                detail["first_record"] = rows[0]
            detail["missing_examples"] = []
            ids = [int(record["id"]) for record in rows]
            existing = {}
            for entity in db.scalars(select(model).where(getattr(model, key).in_(ids))):
                existing.setdefault(getattr(entity, key), []).append(entity)
            for record in rows:
                try:
                    values = normalize_values(model, getattr(adapter, mapper_name)(record))
                except (ValueError, TypeError) as exc:
                    detail["mapping_errors"].append({"id": record["id"], "error": str(exc)})
                    continue
                candidates = existing.get(values[key], [])
                if not candidates:
                    detail["missing"].append(record["id"])
                    if len(detail["missing_examples"]) < 10:
                        detail["missing_examples"].append({k: record.get(k) for k in ["id", "created_at", "updated_at"]})
                elif not any(all(field in IGNORED or getattr(entity, field) == value for field, value in values.items()) for entity in candidates):
                    detail["changed"].append(record["id"])
            report[dataset] = detail
            print(dataset, json.dumps({k: len(v) if isinstance(v, list) and k in {"missing", "changed", "mapping_errors", "newer_than_cursor"} else v
                                       for k, v in detail.items() if k not in {"first_record", "source_meta"}}, default=str), flush=True)
    path = Path("logs/latest_source_audit.json")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("Saved", path)


if __name__ == "__main__":
    main()
