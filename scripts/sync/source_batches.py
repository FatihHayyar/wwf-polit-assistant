"""Stable bulk ID inventories, hydrated from the live API in bounded batches."""
import gzip
import hashlib
import json
import os
import time
from pathlib import Path

import httpx

PAGE_SIZE = 500
EXPORT_INDEX = "https://files.openparldata.ch/exports/index.json"


def request(client, url, **kwargs):
    for attempt in range(5):
        try:
            response = client.get(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in {429, 500, 502, 503, 504} or attempt == 4:
                raise
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError):
            if attempt == 4:
                raise
        time.sleep(min(2 ** attempt, 16))


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    temporary.replace(path)


def job_directory():
    job_id = os.environ.get("SYNC_JOB_ID") or os.environ.get("SYNC_RUN_ID")
    if not job_id:
        return None
    import uuid
    return Path(__file__).resolve().parents[2] / "logs" / "sync_jobs" / uuid.UUID(job_id).hex


class BatchSource:
    def __init__(self, client, url, dataset, full_scan):
        self.client, self.url, self.dataset = client, url, dataset
        self.directory = job_directory()
        self.path = self.directory / f"{dataset}.json" if self.directory else None
        self.state = json.loads(self.path.read_text(encoding="utf-8")) if self.path and self.path.exists() else {}
        self.mode = self.state.get("mode", "inventory" if full_scan else "api")
        self.position = self.state.get("position", 0) if self.mode == "inventory" else 0
        self.ids = None
        self.text_groups = None
        self.next_position = self.position
        self.api_calls = 0
        self.scanned = 0

    def inventory(self):
        inventory_path = self.directory / f"{self.dataset}_ids.json" if self.directory else None
        groups_path = self.directory / "texts_groups.json" if self.directory and self.dataset == "texts" else None
        if inventory_path and inventory_path.exists() and (self.dataset != "texts" or groups_path.exists()):
            self.ids = json.loads(inventory_path.read_text(encoding="utf-8"))
            if groups_path:
                self.text_groups = json.loads(groups_path.read_text(encoding="utf-8"))
            return
        entity = "docs" if self.dataset == "documents" else self.dataset
        manifest = request(self.client, EXPORT_INDEX).json()
        exports = []
        for entry in manifest["files"]:
            if entry["entity"] == entity and entry["format"] == "ndjson.gz":
                exports.extend(entry["files"] if entry.get("type") == "split" else [entry])
        if not exports:
            raise RuntimeError(f"No bulk inventory for {entity}")
        directory = self.directory
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            directory = directory or Path(temporary)
            directory.mkdir(parents=True, exist_ok=True)
            ids = set()
            text_groups = set()
            for entry in exports:
                print(f"{self.dataset}: inventory file {entry.get('filename', '?')}", flush=True)
                export_url = entry["url"]
                if not export_url.startswith("https://files.openparldata.ch/exports/"):
                    raise ValueError("Unexpected export host")
                path = directory / (hashlib.sha256(export_url.encode()).hexdigest() + ".ndjson.gz")
                if not path.exists():
                    for attempt in range(5):
                        try:
                            with self.client.stream("GET", export_url) as response:
                                response.raise_for_status()
                                with path.with_suffix(".download").open("wb") as output:
                                    for chunk in response.iter_bytes():
                                        output.write(chunk)
                            path.with_suffix(".download").replace(path)
                            break
                        except (httpx.TransportError, httpx.HTTPStatusError):
                            if attempt == 4:
                                raise
                            time.sleep(min(2 ** attempt, 16))
                count = 0
                try:
                    with gzip.open(path, "rt", encoding="utf-8") as source:
                        for line in source:
                            if line.strip():
                                record = json.loads(line)
                                ids.add(int(record["id"]))
                                if self.dataset == "texts":
                                    text_groups.add(f"a:{record['affair_id']}" if record.get("affair_id") is not None else f"t:{record['id']}")
                                count += 1
                    if entry.get("row_count") is not None and count != int(entry["row_count"]):
                        raise ValueError("Bulk inventory row count mismatch")
                except (EOFError, gzip.BadGzipFile, ValueError):
                    path.unlink(missing_ok=True)
                    raise
            # Include new IDs created after the daily export. Unsupported filtering
            # parameters are deliberately avoided: this API silently ignores them.
            bulk_max = max(ids, default=0)
            offset = 0
            while True:
                data = request(self.client, self.url, params={"sort_by": "-id", "offset": offset, "limit": PAGE_SIZE}).json()
                rows = data["data"]
                ids.update(int(row["id"]) for row in rows)
                if self.dataset == "texts":
                    text_groups.update(f"a:{row['affair_id']}" if row.get("affair_id") is not None else f"t:{row['id']}" for row in rows)
                if not rows or len(rows) < PAGE_SIZE or min(int(row["id"]) for row in rows) <= bulk_max:
                    break
                offset += PAGE_SIZE
            self.ids = sorted(ids, reverse=True)
            self.text_groups = sorted(text_groups) if self.dataset == "texts" else None
        if inventory_path:
            atomic_json(inventory_path, self.ids)
        if groups_path:
            atomic_json(groups_path, self.text_groups)
        print(f"{self.dataset}: stable inventory={len(self.ids)}; live API hydration", flush=True)

    def next(self, sort_by):
        if self.mode == "api":
            try:
                data = request(self.client, self.url, params={"offset": self.position, "limit": PAGE_SIZE, "sort_by": sort_by}).json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code != 400 or not exc.response.json().get("type", "").endswith("offset-cap-exceeded"):
                    raise
                self.mode, self.position = "inventory", 0
                return self.next(sort_by)
            self.api_calls += 1
            rows = data["data"]
            self.next_position = self.position + len(rows)
            self.scanned += len(rows)
            return rows, not data.get("meta", {}).get("has_more", len(rows) == PAGE_SIZE)
        if self.ids is None:
            self.inventory()
        if self.dataset == "texts":
            return self.next_texts()
        ids = self.ids[self.position:self.position + PAGE_SIZE]
        if not ids:
            return [], True
        data = request(self.client, self.url, params={"id": ",".join(map(str, ids)), "offset": 0, "limit": PAGE_SIZE, "sort_by": "-id"}).json()
        self.api_calls += 1
        rows = data["data"]
        if any(int(row["id"]) not in ids for row in rows):
            raise ValueError("Upstream API ignored the ID filter")
        if data.get("meta", {}).get("has_more", False):
            raise ValueError("ID batch has more records than the API limit; refusing incomplete processing")
        self.next_position = self.position + len(ids)
        self.scanned += len(rows)
        return rows, self.next_position >= len(self.ids)

    def next_texts(self):
        groups = self.text_groups[self.position:self.position + PAGE_SIZE]
        if not groups:
            return [], True
        affairs = [group[2:] for group in groups if group.startswith("a:")]
        rows = []
        if affairs:
            offset = 0
            while True:
                data = request(self.client, self.url, params={"affair_id": ",".join(affairs),
                    "offset": offset, "limit": PAGE_SIZE, "sort_by": "-id"}).json()
                self.api_calls += 1
                batch = data["data"]
                if any(str(row.get("affair_id")) not in affairs for row in batch):
                    raise ValueError("Texts API ignored the affair filter")
                rows.extend(batch)
                # Texts metadata reports global totals even with a filter.
                if len(batch) < PAGE_SIZE:
                    break
                offset += PAGE_SIZE
        for group in groups:
            if group.startswith("t:"):
                try:
                    row = request(self.client, self.url.rstrip("/") + "/" + group[2:]).json()
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 404:
                        continue
                    raise
                if str(row["id"]) != group[2:]:
                    raise ValueError("Texts detail returned an unexpected ID")
                rows.append(row); self.api_calls += 1
        self.scanned += len(rows)
        self.next_position = self.position + len(groups)
        return rows, self.next_position >= len(self.text_groups)

    def commit(self, worker_state):
        # Called only AFTER database commit. A crash before this save replays
        # already committed data; it cannot skip uncommitted records.
        self.position = self.next_position
        self.state = dict(worker_state, mode=self.mode, position=self.position)
        if self.path:
            atomic_json(self.path, self.state)


def make_source(client, url, dataset, full_scan):
    return BatchSource(client, url, dataset, full_scan)
