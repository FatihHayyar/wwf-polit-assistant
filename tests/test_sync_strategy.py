"""Sync phases against a simulated OpenParlData API.

The fake API implements the behaviour verified against the live service on
21 October 2026: ``sort_by`` with ``-`` prefixes (NULLs first when descending),
``exclude_null``, comma-separated ``id`` filters, ``offset``/``limit`` and
``meta.total_records`` after filtering.
"""
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import httpx
from sqlalchemy import BigInteger, create_engine, func, select, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (registers all tables on Base.metadata)
from app.db.database import Base
from app.models.change_event import ChangeEvent
from app.models.entities import Affair, Agenda, Voting
from scripts.seed_classification import seed_taxonomy
from scripts.sync import entity_sync
from scripts.sync.source_batches import BatchSource, atomic_json


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


NOW = datetime(2026, 10, 22, 6, 0)


class FakeApi:
    def __init__(self, records):
        self.records = records
        self.requests = []

    def __call__(self, request):
        params = request.url.params
        self.requests.append(dict(params))
        rows = list(self.records)
        if "id" in params:
            wanted = {int(value) for value in params["id"].split(",")}
            rows = [row for row in rows if row["id"] in wanted]
        if params.get("exclude_null"):
            rows = [row for row in rows if row.get(params["exclude_null"]) is not None]
        for field in reversed(params.get("sort_by", "id").split(",")):
            name = field.lstrip("-")
            descending = field.startswith("-")
            present = sorted((row for row in rows if row.get(name) is not None),
                             key=lambda row: row[name], reverse=descending)
            missing = [row for row in rows if row.get(name) is None]
            rows = missing + present if descending else present + missing
        offset, limit = int(params.get("offset", 0)), int(params.get("limit", 500))
        page = rows[offset:offset + limit]
        return httpx.Response(200, json={"data": page, "meta": {
            "total_records": len(rows), "has_more": offset + limit < len(rows)}})


def voting(record_id, updated_at=None, title="Abstimmung"):
    return {"id": record_id, "body_id": 1, "title": {"de": f"{title} {record_id}"}, "updated_at": updated_at}


class SyncStrategyTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        seed_taxonomy(self.db)
        self.db.execute(text("""CREATE TABLE sync_checkpoints (dataset TEXT PRIMARY KEY, last_updated_at TIMESTAMP,
            last_id BIGINT, last_run_at TIMESTAMP, status TEXT, records_processed BIGINT, records_new BIGINT,
            records_changed BIGINT, records_unchanged BIGINT, records_error BIGINT, error_message TEXT,
            last_full_scan_at TIMESTAMP)"""))
        self.db.commit()
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def checkpoint(self, dataset, updated_at=None, last_id=0, full_scan_at=datetime(2026, 10, 21)):
        self.db.execute(text("""INSERT INTO sync_checkpoints (dataset, last_updated_at, last_id, status, last_full_scan_at)
            VALUES (:d, :u, :i, 'idle', :f)"""), {"d": dataset, "u": updated_at, "i": last_id, "f": full_scan_at})
        self.db.commit()

    def run_sync(self, dataset, api, recheck=False, page_size=500):
        client = httpx.Client(transport=httpx.MockTransport(api))
        self.addCleanup(client.close)
        with patch("scripts.sync.entity_sync.SessionLocal", side_effect=lambda: Session(self.engine, autoflush=False)), \
                patch("scripts.sync.incremental_sync.SessionLocal", side_effect=lambda: Session(self.engine, autoflush=False)), \
                patch("scripts.sync.source_batches.job_directory", return_value=Path(self.folder.name)), \
                patch("scripts.sync.source_batches.PAGE_SIZE", page_size), \
                patch("scripts.sync.entity_sync.make_source",
                      side_effect=lambda _, url, name, full: BatchSource(client, url, name, full)):
            entity_sync.run_dataset(dataset, recheck=recheck, now=NOW)
        self.db.expire_all()

    def row(self, dataset):
        return self.db.execute(text("SELECT last_updated_at, last_id, status, last_full_scan_at, records_new, records_changed "
                                    "FROM sync_checkpoints WHERE dataset=:d"), {"d": dataset}).one()

    def test_incremental_phase_skips_null_timestamps_and_stops_at_checkpoint(self):
        self.checkpoint("votings", "2026-10-20 00:00:00", 5)
        self.db.add_all([Voting(id=1, body_id=1, title_de="Alt 1"), Voting(id=2, body_id=1, title_de="Abstimmung 2")])
        self.db.commit()
        api = FakeApi([voting(1, None, "Neu"), voting(2, "2026-10-21T08:00:00"), voting(3, "2026-10-19T00:00:00")])
        self.run_sync("votings", api, page_size=1)
        incremental = [params for params in api.requests if params.get("exclude_null") == "updated_at"]
        self.assertTrue(incremental)
        self.assertTrue(all(params["sort_by"] == "-updated_at,-id" for params in incremental))
        # Voting 1 changed without a timestamp: only a full scan finds it.
        self.assertEqual(self.db.get(Voting, 1).title_de, "Alt 1")
        # Voting 3 is new but older than the checkpoint: the new-identity phase adds it.
        self.assertIsNotNone(self.db.get(Voting, 3))
        updated_at, last_id, status, _, new, changed = self.row("votings")
        self.assertEqual((str(updated_at)[:19], last_id, status), ("2026-10-21 08:00:00", 2, "idle"))
        self.assertEqual((new, changed), (1, 0))

    def test_new_identity_without_timestamp_is_found(self):
        self.checkpoint("votings", "2026-10-21 00:00:00", 2)
        self.db.add(Voting(id=2, body_id=1, title_de="Abstimmung 2"))
        self.db.commit()
        api = FakeApi([voting(2, "2026-10-20T00:00:00"), voting(7, None)])
        self.run_sync("votings", api)
        self.assertEqual(self.db.get(Voting, 7).title_de, "Abstimmung 7")
        # No export download, no ID inventory.
        self.assertFalse(any("id" in params for params in api.requests))

    def test_full_scan_runs_when_due_and_finds_silent_changes(self):
        self.checkpoint("votings", "2026-10-21 00:00:00", 2, full_scan_at=datetime(2026, 10, 1))
        self.db.add(Voting(id=1, body_id=1, title_de="Alt 1"))
        self.db.commit()
        atomic_json(Path(self.folder.name) / "votings_ids.json", [1])
        api = FakeApi([voting(1, None, "Neu")])
        self.run_sync("votings", api)
        self.assertEqual(self.db.get(Voting, 1).title_de, "Neu 1")
        self.assertEqual(self.db.scalar(select(func.count()).select_from(ChangeEvent)), 1)
        self.assertGreater(str(self.row("votings")[3]), "2026-10-01")

    def test_full_scan_is_skipped_until_due(self):
        self.checkpoint("votings", "2026-10-21 00:00:00", 2, full_scan_at=datetime(2026, 10, 20))
        api = FakeApi([])
        self.run_sync("votings", api)
        self.assertTrue(all("id" not in params for params in api.requests))
        self.assertEqual(str(self.row("votings")[3])[:19], "2026-10-20 00:00:00")

    def test_count_gap_hydrates_only_missing_identities(self):
        self.checkpoint("votings", "2026-10-21 00:00:00", 9)
        self.db.add_all([Voting(id=record_id, body_id=1, title_de=f"Abstimmung {record_id}") for record_id in (1, 3, 9)])
        self.db.commit()
        atomic_json(Path(self.folder.name) / "votings_ids.json", [9, 3, 2, 1])
        api = FakeApi([voting(record_id, "2026-10-01T00:00:00") for record_id in (1, 2, 3, 9)])
        self.run_sync("votings", api)
        self.assertIsNotNone(self.db.get(Voting, 2))
        id_requests = [params["id"] for params in api.requests if "id" in params]
        self.assertEqual(id_requests, ["2"])

    def test_agenda_window_rechecks_current_sessions_only(self):
        self.checkpoint("agendas", None, 3)
        self.db.add_all([Agenda(id=1, body_id=1, item_title="Alt", item_date=datetime(2025, 1, 1)),
                         Agenda(id=2, body_id=1, item_title="Bald", item_date=datetime(2026, 11, 2)),
                         Agenda(id=3, body_id=1, item_title="Ohne Datum")])
        self.db.commit()
        api = FakeApi([
            {"id": 1, "body_id": 1, "item_title": "Alt geändert", "item_date": "2025-01-01T00:00:00"},
            {"id": 2, "body_id": 1, "item_title": "Bald", "item_date": "2026-11-02T00:00:00", "item_result": "Angenommen"},
            {"id": 3, "body_id": 1, "item_title": "Ohne Datum"},
        ])
        self.run_sync("agendas", api, page_size=1)
        self.assertEqual(self.db.get(Agenda, 2).item_result, "Angenommen")
        # Outside the window: left for the weekly full comparison.
        self.assertEqual(self.db.get(Agenda, 1).item_title, "Alt")
        window = [params for params in api.requests if params.get("exclude_null") == "item_date"]
        self.assertLessEqual(len(window), 2)

    def test_affairs_page_is_written_in_one_session(self):
        self.checkpoint("affairs", "2026-10-20 00:00:00", 1)
        api = FakeApi([{"id": record_id, "body_id": 1, "title": {"de": f"Photovoltaik {record_id}"},
                        "updated_at": "2026-10-21T0%d:00:00" % record_id} for record_id in (1, 2, 3)])
        sessions = []

        def session_factory():
            session = Session(self.engine, autoflush=False)
            sessions.append(session)
            return session

        client = httpx.Client(transport=httpx.MockTransport(api))
        self.addCleanup(client.close)
        with patch("scripts.sync.entity_sync.SessionLocal", side_effect=session_factory), \
                patch("scripts.sync.incremental_sync.SessionLocal", side_effect=AssertionError("per-record session")), \
                patch("scripts.sync.source_batches.job_directory", return_value=None), \
                patch("scripts.sync.entity_sync.make_source",
                      side_effect=lambda _, url, name, full: BatchSource(client, url, name, full)):
            entity_sync.run_dataset("affairs", now=NOW)
        self.db.expire_all()
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Affair)), 3)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(ChangeEvent)), 3)
        self.assertEqual(str(self.row("affairs")[0])[:19], "2026-10-21 03:00:00")

    def test_interrupted_missing_phase_resumes_from_saved_candidates(self):
        self.checkpoint("votings", "2026-10-21 00:00:00", 9)
        self.db.add(Voting(id=9, body_id=1, title_de="Abstimmung 9"))
        self.db.commit()
        atomic_json(Path(self.folder.name) / "votings_ids.json", [9, 2, 1])
        api = FakeApi([voting(record_id, "2026-10-01T00:00:00") for record_id in (1, 2, 9)])
        failing = {"armed": True}

        def flaky(request):
            if "id" in request.url.params and failing["armed"]:
                failing["armed"] = False
                raise ValueError("interrupted hydration")
            return api(request)

        with self.assertRaisesRegex(ValueError, "interrupted hydration"):
            self.run_sync("votings", flaky, page_size=1)
        saved = json.loads((Path(self.folder.name) / "votings.json").read_text())
        self.assertEqual(saved["reconciliation_ids"], [2, 1])
        api.requests.clear()
        self.run_sync("votings", api, page_size=1)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Voting)), 3)
        self.assertFalse(any(params.get("sort_by") == "-updated_at,-id" for params in api.requests))


class FullScanScheduleTests(unittest.TestCase):
    def test_intervals(self):
        self.assertTrue(entity_sync.full_scan_due("events", None, NOW))
        self.assertFalse(entity_sync.full_scan_due("events", datetime(2026, 10, 16), NOW))
        self.assertTrue(entity_sync.full_scan_due("events", datetime(2026, 10, 15, 6, 0), NOW))
        self.assertFalse(entity_sync.full_scan_due("documents", None, NOW))
        self.assertTrue(set(entity_sync.FULL_SCAN_DAYS) == set(entity_sync.ADAPTERS))


if __name__ == "__main__":
    unittest.main()
