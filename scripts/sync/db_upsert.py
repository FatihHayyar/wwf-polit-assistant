from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from scripts.sync.dataset_config import DATASETS_BY_NAME

IGNORED_CHANGE_FIELDS = frozenset({"created_at", "updated_at"})
BATCH_SIZE = 500


def upsert_records(
    session: Session,
    dataset_name: str,
    records: Iterable[dict[str, Any]],
) -> int:
    config = DATASETS_BY_NAME[dataset_name]

    if config.requires_special_handling:
        raise ValueError(
            f"{dataset_name} requires a separate safe matching strategy."
        )

    metadata = MetaData()
    table = Table(config.table, metadata, autoload_with=session.bind)

    allowed_columns = set(table.columns.keys())
    key = config.database_key

    if key not in allowed_columns:
        raise ValueError(f"Missing database key: {key}")

    processed = 0
    batch: list[dict[str, Any]] = []

    def write_batch(items: list[dict[str, Any]]) -> None:
        nonlocal processed

        if not items:
            return

        for record in items:
            values = {
                column: value
                for column, value in record.items()
                if column in allowed_columns
            }

            if config.source_key != key:
                values[key] = values.pop(config.source_key)

            if key not in values:
                raise ValueError(f"Missing source key: {config.source_key}")

            statement = insert(table).values(**values)

            update_values = {
                column: getattr(statement.excluded, column)
                for column in values
                if column != key
                and column not in IGNORED_CHANGE_FIELDS
            }

            if update_values:
                statement = statement.on_conflict_do_update(
                    index_elements=[table.c[key]],
                    set_=update_values,
                    where=(
                        __import__("sqlalchemy").or_(
                            *[
                                table.c[column].is_distinct_from(
                                    getattr(statement.excluded, column)
                                )
                                for column in update_values
                            ]
                        )
                    ),
                )
            else:
                statement = statement.on_conflict_do_nothing(
                    index_elements=[table.c[key]]
                )

            session.execute(statement)
            processed += 1

    for record in records:
        batch.append(record)

        if len(batch) >= BATCH_SIZE:
            write_batch(batch)
            batch.clear()

    write_batch(batch)

    return processed
