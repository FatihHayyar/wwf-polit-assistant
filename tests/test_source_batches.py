import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from scripts.sync.source_batches import BatchSource


class SourceBatchTests(unittest.TestCase):
    def test_texts_ignore_global_metadata_and_page_by_supported_affair_filter(self):
        calls=[]
        def handler(request):
            calls.append(request)
            if request.url.path.endswith("/99"):
                return httpx.Response(200,json={"id":99,"affair_id":None})
            self.assertNotIn("id",request.url.params)
            self.assertEqual(request.url.params["affair_id"],"1,2")
            offset=int(request.url.params["offset"])
            rows=[{"id":i,"affair_id":1} for i in range(500)] if offset==0 else [{"id":501,"affair_id":2}]
            return httpx.Response(200,json={"data":rows,"meta":{"has_more":True,"total_records":226062}})
        with httpx.Client(transport=httpx.MockTransport(handler)) as client,patch("scripts.sync.source_batches.job_directory",return_value=None):
            source=BatchSource(client,"https://api.test/texts/","texts",True)
            source.ids=[1];source.text_groups=["a:1","a:2","t:99"]
            rows,finished=source.next("-id")
            self.assertEqual(len(rows),502);self.assertTrue(finished);self.assertEqual(len(calls),3)

    def test_bulk_ids_use_live_contents_and_split_manifest(self):
        requests = []
        def handler(request):
            requests.append(request)
            if request.url.path.endswith("index.json"):
                return httpx.Response(200, json={"files": [{"entity": "agendas", "type": "split", "format": "ndjson.gz", "files": [
                    {"url": "https://files.openparldata.ch/exports/agendas/a.ndjson.gz", "row_count": 2}]}]})
            if request.url.path.endswith(".gz"):
                return httpx.Response(200, content=gzip.compress(b'{"id":1,"title":"stale"}\n{"id":2}\n'))
            if "id" not in request.url.params:
                return httpx.Response(200, json={"data": [{"id": 3}, {"id": 2}], "meta": {"has_more": False}})
            return httpx.Response(200, json={"data": [{"id": 3, "title": "new"}, {"id": 2}, {"id": 1, "title": "live"}], "meta": {"has_more": False}})
        with httpx.Client(transport=httpx.MockTransport(handler)) as client, patch("scripts.sync.source_batches.job_directory", return_value=None):
            source = BatchSource(client, "https://api.openparldata.ch/v1/agendas/", "agendas", True)
            rows, finished = source.next("-id")
            self.assertTrue(finished)
            self.assertEqual(source.ids, [3, 2, 1])
            self.assertEqual(rows[-1]["title"], "live")
            self.assertEqual(requests[-1].url.params["offset"], "0")

    def test_deep_inventory_batch_never_uses_deep_api_offset(self):
        def handler(request):
            self.assertEqual(request.url.params["offset"], "0")
            return httpx.Response(200, json={"data": [{"id": int(i)} for i in request.url.params["id"].split(",")], "meta": {"has_more": False}})
        with httpx.Client(transport=httpx.MockTransport(handler)) as client, patch("scripts.sync.source_batches.job_directory", return_value=None):
            source = BatchSource(client, "https://api.openparldata.ch/v1/events/", "events", True)
            source.ids = list(range(200000, 0, -1))
            source.position = 100500
            rows, finished = source.next("-id")
            self.assertEqual(len(rows), 500)
            self.assertEqual(rows[0]["id"], 99500)
            self.assertFalse(finished)

    def test_progress_does_not_advance_until_committed_and_resumes(self):
        with tempfile.TemporaryDirectory() as folder, patch("scripts.sync.source_batches.job_directory", return_value=Path(folder)):
            with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"data": [{"id": 2}], "meta": {"has_more": False}}))) as client:
                source = BatchSource(client, "https://api.test/", "events", True)
                source.ids = [2, 1]; source.next("-id")
                self.assertFalse(source.path.exists())
                source.commit({"complete": False, "counts": {"UNCHANGED": 1}})
                restored = BatchSource(client, "https://api.test/", "events", True)
                self.assertEqual(restored.position, 2)
                self.assertEqual(restored.state["counts"]["UNCHANGED"], 1)

    def test_ignored_id_filter_fails_instead_of_marking_complete(self):
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"data": [{"id": 999}], "meta": {"has_more": False}}))) as client, patch("scripts.sync.source_batches.job_directory", return_value=None):
            source = BatchSource(client, "https://api.test/", "events", True); source.ids = [1]
            with self.assertRaisesRegex(ValueError, "ignored the ID filter"):
                source.next("-id")

    def test_cap_error_switches_to_inventory_instead_of_stopping(self):
        def handler(request):
            if "id" not in request.url.params:
                return httpx.Response(400, json={"type": "https://api.test/problems/offset-cap-exceeded"})
            return httpx.Response(200, json={"data": [{"id": 1}], "meta": {"has_more": False}})
        with httpx.Client(transport=httpx.MockTransport(handler)) as client, patch("scripts.sync.source_batches.job_directory", return_value=None):
            source = BatchSource(client, "https://api.test/", "meetings", False)
            source.position = 100500; source.ids = [1]
            self.assertEqual(source.next("-updated_at,-id"), ([{"id": 1}], True))
            self.assertEqual(source.mode, "inventory")


if __name__ == "__main__":
    unittest.main()
