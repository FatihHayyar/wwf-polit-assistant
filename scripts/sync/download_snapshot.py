from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from scripts.bootstrap.download_openparldata import (
    collect_dataset_files,
    fetch_manifest,
    run_downloads,
)
from scripts.sync.dataset_config import DATASETS


def download_sync_snapshot(workers: int = 6) -> Path:
    manifest = fetch_manifest()

    datasets = tuple(config.name for config in DATASETS)
    files = collect_dataset_files(manifest, datasets)

    snapshot_name = (
        "sync-"
        + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    )

    results = run_downloads(
        files=files,
        snapshot_name=snapshot_name,
        workers=workers,
    )

    failed = [
        result
        for result in results
        if result.status == "failed"
        or not result.path.is_file()
        or result.path.stat().st_size != result.export_file.size
    ]

    if failed:
        names = ", ".join(
            result.export_file.filename for result in failed
        )
        raise RuntimeError(
            f"Sync snapshot incomplete. Failed files: {names}"
        )

    snapshot_path = Path("data/raw") / snapshot_name

    print(f"Snapshot ready: {snapshot_path}")
    print(f"Verified files: {len(results)}")

    return snapshot_path


if __name__ == "__main__":
    download_sync_snapshot()
