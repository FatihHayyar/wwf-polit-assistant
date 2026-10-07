from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402


RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROGRESS_EVERY = 25_000


@dataclass(frozen=True)
class Dataset:
    name: str
    table: str
    columns: tuple[str, ...]
    subdirectory: str | None = None
    source_columns: tuple[str, ...] | None = None
    shard_commits: bool = False

    @property
    def input_columns(self) -> tuple[str, ...]:
        return self.source_columns or self.columns


DATASETS: dict[str, Dataset] = {
    "bodies": Dataset(
        name="bodies",
        table="bodies",
        columns=(
            "id",
            "body_key",
            "name",
            "name_de",
            "name_fr",
            "name_it",
            "name_en",
            "lang",
            "type",
            "canton_key",
            "country_key",
            "has_parliament",
            "population",
        ),
    ),
    "persons": Dataset(
        name="persons",
        table="persons",
        columns=(
            "id",
            "body_id",
            "body_key",
            "external_id",
            "fullname",
            "firstname",
            "lastname",
            "party_de",
            "party_fr",
            "party_it",
            "party_harmonized_de",
            "party_harmonized_fr",
            "party_harmonized_it",
            "email",
            "city",
            "gender",
            "active",
            "language",
            "wikidata_id",
            "updated_at",
            "created_at",
        ),
    ),
    "groups": Dataset(
        name="groups",
        table="groups",
        columns=(
            "id",
            "body_id",
            "body_key",
            "external_id",
            "type_harmonized",
            "type_harmonized_de",
            "type_harmonized_fr",
            "type_harmonized_it",
            "active",
            "name_de",
            "name_fr",
            "name_it",
            "abbreviation_de",
            "abbreviation_fr",
            "abbreviation_it",
            "updated_at",
            "created_at",
        ),
    ),
    "memberships": Dataset(
        name="memberships",
        table="memberships",
        columns=(
            "id",
            "body_id",
            "body_key",
            "external_id",
            "person_id",
            "person_fullname",
            "group_id",
            "group_name_de",
            "group_name_fr",
            "group_name_it",
            "role_name_de",
            "role_name_fr",
            "role_name_it",
            "begin_date",
            "end_date",
            "active",
            "type_harmonized",
            "updated_at",
            "created_at",
        ),
    ),
    "interests": Dataset(
        name="interests",
        table="interests",
        columns=(
            "id",
            "body_id",
            "body_key",
            "person_id",
            "external_id",
            "type_de",
            "type_fr",
            "type_it",
            "name_de",
            "name_fr",
            "name_it",
            "url",
            "role_name_de",
            "role_name_fr",
            "role_name_it",
            "begin_date",
            "end_date",
            "declaration_doc_url",
            "declaration_doc_title",
            "place",
            "ex_officio",
            "updated_at",
            "created_at",
        ),
    ),
    "affairs": Dataset(
        name="affairs",
        table="affairs",
        columns=(
            "id",
            "body_id",
            "body_key",
            "number",
            "external_id",
            "external_alternative_id",
            "title_de",
            "title_fr",
            "title_it",
            "title_rm",
            "title_long_de",
            "title_long_fr",
            "title_long_it",
            "title_long_rm",
            "type_name_de",
            "type_name_fr",
            "type_name_it",
            "type_harmonized_de",
            "type_harmonized_fr",
            "type_harmonized_it",
            "type_harmonized_en",
            "state_name_de",
            "state_name_fr",
            "state_name_it",
            "state_name_harmonized_de",
            "state_name_harmonized_fr",
            "state_name_harmonized_it",
            "begin_date",
            "end_date",
            "active",
            "url_external_de",
            "url_external_fr",
            "url_external_it",
            "updated_at",
            "created_at",
        ),
    ),
    "meetings": Dataset(
        name="meetings",
        table="meetings",
        columns=(
            "id",
            "body_id",
            "body_key",
            "external_id",
            "type",
            "parent_type",
            "parent_external_id",
            "number",
            "abbreviation",
            "name_de",
            "name_fr",
            "name_it",
            "name_rm",
            "group_id",
            "begin_date",
            "end_date",
            "state",
            "description_de",
            "description_fr",
            "description_it",
            "location",
            "updated_at",
            "created_at",
        ),
    ),
    "agendas": Dataset(
        name="agendas",
        table="agendas",
        columns=(
            "id",
            "body_id",
            "body_key",
            "meeting_id",
            "item_date",
            "item_external_id",
            "item_title",
            "item_number_display",
            "item_number",
            "item_description",
            "item_status",
            "item_result",
            "item_category",
            "item_url",
            "item_affair_number",
            "item_affair_id",
            "item_language",
            "created_at",
        ),
    ),
    "events": Dataset(
        name="events",
        table="events",
        columns=(
            "id",
            "body_id",
            "body_key",
            "external_id",
            "date",
            "position",
            "title_de",
            "title_fr",
            "title_it",
            "title_harmonized",
            "title_harmonized_de",
            "title_harmonized_fr",
            "title_harmonized_it",
            "title_harmonized_en",
            "last",
            "actor_de",
            "actor_fr",
            "actor_it",
            "actor_type",
            "affair_id",
            "meeting_id",
            "details_url",
            "details_text",
            "updated_at",
            "created_at",
        ),
    ),
    "votings": Dataset(
        name="votings",
        table="votings",
        columns=(
            "id",
            "body_id",
            "body_key",
            "external_id",
            "date",
            "affair_id",
            "title_de",
            "title_fr",
            "title_it",
            "type_de",
            "type_fr",
            "type_it",
            "meaning_of_yes_de",
            "meaning_of_yes_fr",
            "meaning_of_yes_it",
            "meaning_of_no_de",
            "meaning_of_no_fr",
            "meaning_of_no_it",
            "results_yes",
            "results_no",
            "results_abstention",
            "results_absent",
            "results_string",
            "decision",
            "meeting_id",
            "group_id",
            "updated_at",
            "created_at",
        ),
    ),
    "docs": Dataset(
        name="docs",
        table="documents",
        columns=(
            "source_id",
            "url",
            "date",
            "hash",
            "name",
            "size",
            "text",
            "format",
            "body_id",
            "body_key",
            "language",
            "affair_id",
            "agenda_id",
            "meeting_id",
            "url_oparl",
            "updated_at",
            "category_de",
            "category_fr",
            "category_it",
            "external_id",
            "parent_type",
            "category_harmonized",
        ),
        source_columns=(
            "id",
            "url",
            "date",
            "hash",
            "name",
            "size",
            "text",
            "format",
            "body_id",
            "body_key",
            "language",
            "affair_id",
            "agenda_id",
            "meeting_id",
            "url_oparl",
            "updated_at",
            "category_de",
            "category_fr",
            "category_it",
            "external_id",
            "parent_type",
            "category_harmonized",
        ),
        subdirectory="docs",
        shard_commits=True,
    ),
    "texts": Dataset(
        name="texts",
        table="texts",
        columns=(
            "id",
            "body_id",
            "body_key",
            "affair_id",
            "external_id",
            "text_de",
            "text_fr",
            "text_it",
            "text_rm",
            "type_de",
            "type_fr",
            "type_it",
            "type_rm",
            "text_date",
            "text_format",
            "updated_at",
            "created_at",
        ),
        subdirectory="texts",
        shard_commits=True,
    ),
}


ORDER = (
    "bodies",
    "persons",
    "groups",
    "memberships",
    "interests",
    "affairs",
    "meetings",
    "agendas",
    "events",
    "votings",
    "docs",
    "texts",
)


def database_url() -> str:
    return settings.database_url.replace(
        "postgresql+psycopg://",
        "postgresql://",
    )


def snapshot_dir() -> Path:
    if not RAW_DIR.exists():
        raise RuntimeError(f"Raw directory does not exist: {RAW_DIR}")

    candidates = sorted(
        (
            path
            for path in RAW_DIR.iterdir()
            if path.is_dir()
        ),
        reverse=True,
    )

    for candidate in candidates:
        if (candidate / "bodies.ndjson.gz").exists():
            return candidate

    raise RuntimeError(
        f"No valid OpenParlData snapshot found under {RAW_DIR}"
    )


def dataset_files(snapshot: Path, dataset: Dataset) -> list[Path]:
    if dataset.subdirectory:
        directory = snapshot / dataset.subdirectory
        files = sorted(directory.glob("*.ndjson.gz"))
    else:
        path = snapshot / f"{dataset.name}.ndjson.gz"
        files = [path] if path.exists() else []

    if not files:
        raise RuntimeError(
            f"No files found for dataset '{dataset.name}'"
        )

    return files


def ensure_progress_table(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bootstrap_import_files (
                dataset TEXT NOT NULL,
                snapshot TEXT NOT NULL,
                source_file TEXT NOT NULL,
                row_count BIGINT NOT NULL,
                imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (dataset, snapshot, source_file)
            )
            """
        )

    conn.commit()


def completed_files(
    conn: psycopg.Connection[Any],
    dataset: Dataset,
    snapshot: Path,
) -> dict[str, int]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT source_file, row_count
            FROM bootstrap_import_files
            WHERE dataset = %s
              AND snapshot = %s
            """,
            (dataset.name, snapshot.name),
        )

        return {
            source_file: row_count
            for source_file, row_count in cursor.fetchall()
        }


def mark_file_complete(
    conn: psycopg.Connection[Any],
    dataset: Dataset,
    snapshot: Path,
    path: Path,
    row_count: int,
) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO bootstrap_import_files (
                dataset,
                snapshot,
                source_file,
                row_count
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (dataset, snapshot, source_file)
            DO UPDATE SET
                row_count = EXCLUDED.row_count,
                imported_at = CURRENT_TIMESTAMP
            """,
            (
                dataset.name,
                snapshot.name,
                path.name,
                row_count,
            ),
        )


def existing_rows(
    conn: psycopg.Connection[Any],
    table: str,
) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(table)
            )
        )
        result = cursor.fetchone()

    return int(result[0]) if result else 0


def truncate_table(
    conn: psycopg.Connection[Any],
    table: str,
) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY").format(
                sql.Identifier(table)
            )
        )

    conn.commit()


def clear_progress(
    conn: psycopg.Connection[Any],
    dataset: Dataset,
    snapshot: Path,
) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM bootstrap_import_files
            WHERE dataset = %s
              AND snapshot = %s
            """,
            (dataset.name, snapshot.name),
        )

    conn.commit()


def copy_statement(dataset: Dataset) -> sql.Composed:
    identifiers = [
        sql.Identifier(column)
        for column in dataset.columns
    ]

    return sql.SQL(
        "COPY {} ({}) FROM STDIN"
    ).format(
        sql.Identifier(dataset.table),
        sql.SQL(", ").join(identifiers),
    )


def record_values(
    record: dict[str, Any],
    dataset: Dataset,
) -> tuple[Any, ...]:
    return tuple(
        record.get(source_column)
        for source_column in dataset.input_columns
    )


def import_one_file(
    conn: psycopg.Connection[Any],
    dataset: Dataset,
    path: Path,
    global_rows_before: int,
    global_started: float,
) -> int:
    rows = 0
    file_started = time.perf_counter()

    statement = copy_statement(dataset)

    with conn.cursor() as cursor:
        with cursor.copy(statement) as copy:
            with gzip.open(
                path,
                "rt",
                encoding="utf-8",
            ) as handle:
                for line in handle:
                    record = json.loads(line)

                    copy.write_row(
                        record_values(record, dataset)
                    )

                    rows += 1

                    total_rows = global_rows_before + rows

                    if total_rows % PROGRESS_EVERY == 0:
                        elapsed = (
                            time.perf_counter()
                            - global_started
                        )

                        speed = (
                            total_rows / elapsed
                            if elapsed > 0
                            else 0
                        )

                        print(
                            f"[PROGRESS] {dataset.name}: "
                            f"{total_rows:,} rows | "
                            f"{speed:,.0f} rows/s"
                        )

    file_elapsed = time.perf_counter() - file_started

    print(
        f"{path.name}: "
        f"{rows:,} rows in "
        f"{file_elapsed:.2f}s"
    )

    return rows


def import_sharded_dataset(
    conn: psycopg.Connection[Any],
    snapshot: Path,
    dataset: Dataset,
    files: list[Path],
) -> None:
    ensure_progress_table(conn)

    current = existing_rows(conn, dataset.table)
    done = completed_files(conn, dataset, snapshot)

    # If the table contains data but there is no matching progress state,
    # this is an old/incomplete import. Reset it once.
    if current > 0 and not done:
        print(
            f"[RESET] {dataset.table} contains "
            f"{current:,} rows without resume state."
        )
        truncate_table(conn, dataset.table)
        current = 0

    # If progress state exists but the table is empty, the progress state
    # cannot be trusted.
    if current == 0 and done:
        print(
            "[RESET] Resume state exists but table is empty. "
            "Clearing resume state."
        )
        clear_progress(conn, dataset, snapshot)
        done = {}

    imported_this_run = 0
    skipped_rows = sum(done.values())
    started = time.perf_counter()

    print(
        f"Already committed: {len(done)}/{len(files)} files, "
        f"{skipped_rows:,} rows"
    )

    for index, path in enumerate(files, start=1):
        if path.name in done:
            print(
                f"[SKIP] {index}/{len(files)} "
                f"{path.name}: "
                f"{done[path.name]:,} rows already committed"
            )
            continue

        before = skipped_rows + imported_this_run

        try:
            rows = import_one_file(
                conn=conn,
                dataset=dataset,
                path=path,
                global_rows_before=before,
                global_started=started,
            )

            mark_file_complete(
                conn=conn,
                dataset=dataset,
                snapshot=snapshot,
                path=path,
                row_count=rows,
            )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        imported_this_run += rows

        print(
            f"[COMMIT] {index}/{len(files)} "
            f"{path.name}: {rows:,} rows"
        )

    actual = existing_rows(conn, dataset.table)
    expected = skipped_rows + imported_this_run
    elapsed = time.perf_counter() - started

    print()
    print(f"Imported this run: {imported_this_run:,}")
    print(f"Expected DB rows:  {expected:,}")
    print(f"Database rows:     {actual:,}")
    print(f"Time this run:     {elapsed:.2f}s")

    if actual != expected:
        raise RuntimeError(
            f"Validation failed for {dataset.name}: "
            f"expected {expected:,}, found {actual:,}"
        )

    print("[VALIDATION OK]")


def import_regular_dataset(
    conn: psycopg.Connection[Any],
    snapshot: Path,
    dataset: Dataset,
    files: list[Path],
) -> None:
    current = existing_rows(conn, dataset.table)

    if current:
        print(
            f"[RESET] {dataset.table} contains "
            f"{current:,} rows."
        )
        truncate_table(conn, dataset.table)

    total_rows = 0
    started = time.perf_counter()

    try:
        statement = copy_statement(dataset)

        with conn.cursor() as cursor:
            with cursor.copy(statement) as copy:
                for index, path in enumerate(files, start=1):
                    file_rows = 0
                    file_started = time.perf_counter()

                    with gzip.open(
                        path,
                        "rt",
                        encoding="utf-8",
                    ) as handle:
                        for line in handle:
                            record = json.loads(line)

                            copy.write_row(
                                record_values(
                                    record,
                                    dataset,
                                )
                            )

                            total_rows += 1
                            file_rows += 1

                            if (
                                total_rows
                                % PROGRESS_EVERY
                                == 0
                            ):
                                elapsed = (
                                    time.perf_counter()
                                    - started
                                )

                                speed = (
                                    total_rows / elapsed
                                    if elapsed > 0
                                    else 0
                                )

                                print(
                                    f"[PROGRESS] "
                                    f"{dataset.name}: "
                                    f"{total_rows:,} rows | "
                                    f"{speed:,.0f} rows/s"
                                )

                    file_elapsed = (
                        time.perf_counter()
                        - file_started
                    )

                    print(
                        f"[FILE] {index}/{len(files)} "
                        f"{path.name}: "
                        f"{file_rows:,} rows in "
                        f"{file_elapsed:.2f}s"
                    )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    actual = existing_rows(conn, dataset.table)
    elapsed = time.perf_counter() - started

    print()
    print(f"Imported:      {total_rows:,}")
    print(f"Database rows: {actual:,}")
    print(f"Time:          {elapsed:.2f}s")

    if actual != total_rows:
        raise RuntimeError(
            f"Validation failed for {dataset.name}: "
            f"expected {total_rows:,}, found {actual:,}"
        )

    speed = total_rows / elapsed if elapsed > 0 else 0

    print(f"Throughput:    {speed:,.0f} rows/s")
    print("[VALIDATION OK]")


def import_dataset(
    conn: psycopg.Connection[Any],
    snapshot: Path,
    dataset: Dataset,
) -> None:
    files = dataset_files(snapshot, dataset)
    current = existing_rows(conn, dataset.table)

    print()
    print("=" * 78)
    print(f"DATASET:       {dataset.name}")
    print(f"TABLE:         {dataset.table}")
    print(f"FILES:         {len(files)}")
    print(f"CURRENT:       {current:,}")
    print("=" * 78)

    if dataset.shard_commits:
        import_sharded_dataset(
            conn=conn,
            snapshot=snapshot,
            dataset=dataset,
            files=files,
        )
    else:
        import_regular_dataset(
            conn=conn,
            snapshot=snapshot,
            dataset=dataset,
            files=files,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import OpenParlData raw NDJSON snapshots "
            "into normalized PostgreSQL tables."
        )
    )

    parser.add_argument(
        "dataset",
        choices=(*ORDER, "all"),
        help="Dataset to import.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = snapshot_dir()

    selected = (
        ORDER
        if args.dataset == "all"
        else (args.dataset,)
    )

    print(f"Snapshot: {snapshot.name}")

    with psycopg.connect(database_url()) as conn:
        for dataset_name in selected:
            import_dataset(
                conn=conn,
                snapshot=snapshot,
                dataset=DATASETS[dataset_name],
            )

    print()
    print("=" * 78)
    print("NORMALIZED IMPORT COMPLETE")
    print("=" * 78)


if __name__ == "__main__":
    main()