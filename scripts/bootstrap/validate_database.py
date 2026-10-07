from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402


EXPECTED_COUNTS = {
    "bodies": 2_411,
    "persons": 26_864,
    "groups": 8_885,
    "memberships": 121_456,
    "interests": 30_343,
    "affairs": 325_691,
    "meetings": 33_670,
    "agendas": 422_971,
    "events": 915_238,
    "votings": 77_061,
    "documents": 907_736,
    "texts": 225_739,
}


def database_url() -> str:
    return settings.database_url.replace(
        "postgresql+psycopg://",
        "postgresql://",
    )


def scalar(
    conn: psycopg.Connection[Any],
    query: str,
) -> int:
    with conn.cursor() as cursor:
        cursor.execute(query)
        row = cursor.fetchone()

    return int(row[0]) if row else 0


def print_check(
    name: str,
    actual: int,
    expected: int = 0,
) -> bool:
    ok = actual == expected
    status = "OK" if ok else "FAIL"

    print(
        f"[{status:4}] "
        f"{name:<55} "
        f"{actual:>12,}"
    )

    return ok


def main() -> None:
    started = time.perf_counter()
    failures = 0

    with psycopg.connect(database_url()) as conn:
        print()
        print("=" * 82)
        print("1. ROW COUNTS")
        print("=" * 82)

        total = 0

        for table, expected in EXPECTED_COUNTS.items():
            actual = scalar(
                conn,
                f'SELECT COUNT(*) FROM "{table}"',
            )

            total += actual

            if not print_check(
                f"{table} rows",
                actual,
                expected,
            ):
                failures += 1

        expected_total = sum(EXPECTED_COUNTS.values())

        if not print_check(
            "TOTAL rows",
            total,
            expected_total,
        ):
            failures += 1

        print()
        print("=" * 82)
        print("2. PRIMARY IDENTIFIERS")
        print("=" * 82)

        unique_checks = {
            "bodies duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM bodies
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
            "persons duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM persons
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
            "groups duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM groups
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
            "memberships duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM memberships
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
            "interests duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM interests
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
            "affairs duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM affairs
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
            "meetings duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM meetings
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
            "agendas duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM agendas
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
            "events duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM events
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
            "votings duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM votings
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
            "texts duplicate id": """
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM texts
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) x
            """,
        }

        for name, query in unique_checks.items():
            actual = scalar(conn, query)

            if not print_check(name, actual):
                failures += 1

        print()
        print("=" * 82)
        print("3. RELATIONSHIP CHECKS")
        print("=" * 82)

        relationship_checks = {
            "affairs -> missing body": """
                SELECT COUNT(*)
                FROM affairs a
                LEFT JOIN bodies b
                    ON b.id = a.body_id
                WHERE a.body_id IS NOT NULL
                  AND b.id IS NULL
            """,
            "persons -> missing body": """
                SELECT COUNT(*)
                FROM persons p
                LEFT JOIN bodies b
                    ON b.id = p.body_id
                WHERE p.body_id IS NOT NULL
                  AND b.id IS NULL
            """,
            "groups -> missing body": """
                SELECT COUNT(*)
                FROM groups g
                LEFT JOIN bodies b
                    ON b.id = g.body_id
                WHERE g.body_id IS NOT NULL
                  AND b.id IS NULL
            """,
            "meetings -> missing body": """
                SELECT COUNT(*)
                FROM meetings m
                LEFT JOIN bodies b
                    ON b.id = m.body_id
                WHERE m.body_id IS NOT NULL
                  AND b.id IS NULL
            """,
            "agendas -> missing meeting": """
                SELECT COUNT(*)
                FROM agendas a
                LEFT JOIN meetings m
                    ON m.id = a.meeting_id
                WHERE a.meeting_id IS NOT NULL
                  AND m.id IS NULL
            """,
            "agendas -> missing affair": """
                SELECT COUNT(*)
                FROM agendas a
                LEFT JOIN affairs af
                    ON af.id = a.item_affair_id
                WHERE a.item_affair_id IS NOT NULL
                  AND af.id IS NULL
            """,
            "events -> missing affair": """
                SELECT COUNT(*)
                FROM events e
                LEFT JOIN affairs a
                    ON a.id = e.affair_id
                WHERE e.affair_id IS NOT NULL
                  AND a.id IS NULL
            """,
            "events -> missing meeting": """
                SELECT COUNT(*)
                FROM events e
                LEFT JOIN meetings m
                    ON m.id = e.meeting_id
                WHERE e.meeting_id IS NOT NULL
                  AND m.id IS NULL
            """,
            "votings -> missing affair": """
                SELECT COUNT(*)
                FROM votings v
                LEFT JOIN affairs a
                    ON a.id = v.affair_id
                WHERE v.affair_id IS NOT NULL
                  AND a.id IS NULL
            """,
            "votings -> missing meeting": """
                SELECT COUNT(*)
                FROM votings v
                LEFT JOIN meetings m
                    ON m.id = v.meeting_id
                WHERE v.meeting_id IS NOT NULL
                  AND m.id IS NULL
            """,
            "memberships -> missing person": """
                SELECT COUNT(*)
                FROM memberships m
                LEFT JOIN persons p
                    ON p.id = m.person_id
                WHERE m.person_id IS NOT NULL
                  AND p.id IS NULL
            """,
            "memberships -> missing group": """
                SELECT COUNT(*)
                FROM memberships m
                LEFT JOIN groups g
                    ON g.id = m.group_id
                WHERE m.group_id IS NOT NULL
                  AND g.id IS NULL
            """,
            "interests -> missing person": """
                SELECT COUNT(*)
                FROM interests i
                LEFT JOIN persons p
                    ON p.id = i.person_id
                WHERE i.person_id IS NOT NULL
                  AND p.id IS NULL
            """,
            "documents -> missing body": """
                SELECT COUNT(*)
                FROM documents d
                LEFT JOIN bodies b
                    ON b.id = d.body_id
                WHERE d.body_id IS NOT NULL
                  AND b.id IS NULL
            """,
            "documents -> missing affair": """
                SELECT COUNT(*)
                FROM documents d
                LEFT JOIN affairs a
                    ON a.id = d.affair_id
                WHERE d.affair_id IS NOT NULL
                  AND a.id IS NULL
            """,
            "documents -> missing agenda": """
                SELECT COUNT(*)
                FROM documents d
                LEFT JOIN agendas a
                    ON a.id = d.agenda_id
                WHERE d.agenda_id IS NOT NULL
                  AND a.id IS NULL
            """,
            "documents -> missing meeting": """
                SELECT COUNT(*)
                FROM documents d
                LEFT JOIN meetings m
                    ON m.id = d.meeting_id
                WHERE d.meeting_id IS NOT NULL
                  AND m.id IS NULL
            """,
            "texts -> missing body": """
                SELECT COUNT(*)
                FROM texts t
                LEFT JOIN bodies b
                    ON b.id = t.body_id
                WHERE t.body_id IS NOT NULL
                  AND b.id IS NULL
            """,
            "texts -> missing affair": """
                SELECT COUNT(*)
                FROM texts t
                LEFT JOIN affairs a
                    ON a.id = t.affair_id
                WHERE t.affair_id IS NOT NULL
                  AND a.id IS NULL
            """,
        }

        for name, query in relationship_checks.items():
            actual = scalar(conn, query)

            if not print_check(name, actual):
                failures += 1

        print()
        print("=" * 82)
        print("4. DOCUMENT IMPORT CHECK")
        print("=" * 82)

        document_rows = scalar(
            conn,
            "SELECT COUNT(*) FROM documents",
        )

        unique_source_ids = scalar(
            conn,
            """
            SELECT COUNT(DISTINCT source_id)
            FROM documents
            """,
        )

        repeated_source_ids = scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM (
                SELECT source_id
                FROM documents
                GROUP BY source_id
                HAVING COUNT(*) > 1
            ) x
            """,
        )

        print_check(
            "documents total",
            document_rows,
            907_736,
        )

        print_check(
            "documents unique source_id",
            unique_source_ids,
            901_578,
        )

        print_check(
            "documents repeated source_id groups",
            repeated_source_ids,
            5_881,
        )

        if document_rows != 907_736:
            failures += 1

        if unique_source_ids != 901_578:
            failures += 1

        if repeated_source_ids != 5_881:
            failures += 1

        print()
        print("=" * 82)
        print("5. BASIC CONTENT CHECKS")
        print("=" * 82)

        content_checks = {
            "bodies without id": """
                SELECT COUNT(*)
                FROM bodies
                WHERE id IS NULL
            """,
            "affairs without id": """
                SELECT COUNT(*)
                FROM affairs
                WHERE id IS NULL
            """,
            "documents without source_id": """
                SELECT COUNT(*)
                FROM documents
                WHERE source_id IS NULL
            """,
            "texts without id": """
                SELECT COUNT(*)
                FROM texts
                WHERE id IS NULL
            """,
        }

        for name, query in content_checks.items():
            actual = scalar(conn, query)

            if not print_check(name, actual):
                failures += 1

    elapsed = time.perf_counter() - started

    print()
    print("=" * 82)

    if failures == 0:
        print("DATABASE VALIDATION: PASSED")
    else:
        print(
            f"DATABASE VALIDATION: "
            f"FAILED ({failures} checks)"
        )

    print(f"Time: {elapsed:.2f}s")
    print("=" * 82)

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()