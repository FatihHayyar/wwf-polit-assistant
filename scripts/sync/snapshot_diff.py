from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


IGNORED_CHANGE_FIELDS = {"created_at", "updated_at"}


@dataclass
class SyncChanges:
    entity: str
    new: list[dict[str, Any]]
    changed: list[dict[str, Any]]
    deleted_ids: list[int]

    @property
    def summary(self) -> dict[str, int | str]:
        return {
            "entity": self.entity,
            "new": len(self.new),
            "changed": len(self.changed),
            "deleted": len(self.deleted_ids),
        }


def read_records(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield json.loads(line)


def record_key(record: dict[str, Any], entity: str) -> int:
    if entity == "documents":
        return int(record["id"])

    return int(record["id"])


def meaningful_content(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.items()
        if key not in IGNORED_CHANGE_FIELDS
    }


def compare_snapshots(
    entity: str,
    old_path: Path,
    new_path: Path,
) -> SyncChanges:
    old_records = {
        record_key(record, entity): record
        for record in read_records(old_path)
    }

    new_records = {
        record_key(record, entity): record
        for record in read_records(new_path)
    }

    old_ids = old_records.keys()
    new_ids = new_records.keys()

    new = [
        new_records[record_id]
        for record_id in new_ids - old_ids
    ]

    changed = [
        new_records[record_id]
        for record_id in new_ids & old_ids
        if meaningful_content(new_records[record_id])
        != meaningful_content(old_records[record_id])
    ]

    deleted_ids = sorted(old_ids - new_ids)

    return SyncChanges(
        entity=entity,
        new=new,
        changed=changed,
        deleted_ids=deleted_ids,
    )
