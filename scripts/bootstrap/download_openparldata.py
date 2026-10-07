from __future__ import annotations

import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


MANIFEST_URL = "https://files.openparldata.ch/exports/index.json"

DEFAULT_DATASETS = (
    "bodies",
    "persons",
    "memberships",
    "groups",
    "interests",
    "affairs",
    "meetings",
    "agendas",
    "events",
    "votings",
    "docs",
    "texts",
)

RAW_DATA_DIR = Path("data/raw")

DEFAULT_WORKERS = 6
CHUNK_SIZE = 1024 * 1024
CONNECT_TIMEOUT = 30.0
READ_TIMEOUT = 120.0
MAX_ATTEMPTS = 3

print_lock = threading.Lock()


@dataclass(frozen=True)
class ExportFile:
    dataset: str
    filename: str
    url: str
    size: int
    row_count: int


@dataclass(frozen=True)
class DownloadResult:
    export_file: ExportFile
    status: str
    path: Path
    message: str = ""


class DownloadProgress:
    def __init__(self, total_files: int, total_bytes: int) -> None:
        self.total_files = total_files
        self.total_bytes = total_bytes

        self.completed_files = 0
        self.completed_bytes = 0
        self.downloaded_files = 0
        self.skipped_files = 0
        self.failed_files = 0

        self.started_at = time.monotonic()
        self.lock = threading.Lock()

    def add_result(self, result: DownloadResult) -> None:
        with self.lock:
            self.completed_files += 1

            if result.status in {"downloaded", "skipped"}:
                self.completed_bytes += result.export_file.size

            if result.status == "downloaded":
                self.downloaded_files += 1
            elif result.status == "skipped":
                self.skipped_files += 1
            elif result.status == "failed":
                self.failed_files += 1

            self.print_progress()

    def print_progress(self) -> None:
        elapsed = max(
            time.monotonic() - self.started_at,
            0.001,
        )

        percentage = (
            (self.completed_bytes / self.total_bytes) * 100
            if self.total_bytes
            else 100.0
        )

        average_speed = self.completed_bytes / elapsed

        remaining_bytes = max(
            self.total_bytes - self.completed_bytes,
            0,
        )

        if average_speed > 0:
            eta_seconds = remaining_bytes / average_speed
            eta = format_duration(eta_seconds)
        else:
            eta = "--:--:--"

        safe_print(
            "[PROGRESS] "
            f"{self.completed_files}/{self.total_files} files | "
            f"{percentage:6.2f}% | "
            f"{format_bytes(self.completed_bytes)} / "
            f"{format_bytes(self.total_bytes)} | "
            f"{format_bytes(int(average_speed))}/s | "
            f"ETA {eta}"
        )


def safe_print(message: str) -> None:
    with print_lock:
        print(message, flush=True)


def format_bytes(size: int) -> str:
    value = float(size)

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} TB"


def format_duration(seconds: float) -> str:
    seconds_int = max(int(seconds), 0)

    hours, remainder = divmod(seconds_int, 3600)
    minutes, seconds_left = divmod(remainder, 60)

    return f"{hours:02}:{minutes:02}:{seconds_left:02}"


def fetch_manifest() -> dict[str, Any]:
    safe_print(f"Fetching manifest: {MANIFEST_URL}")

    timeout = httpx.Timeout(
        connect=CONNECT_TIMEOUT,
        read=READ_TIMEOUT,
        write=READ_TIMEOUT,
        pool=READ_TIMEOUT,
    )

    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        response = client.get(MANIFEST_URL)
        response.raise_for_status()
        return response.json()


def get_snapshot_name(manifest: dict[str, Any]) -> str:
    generated_at = manifest.get("generated_at")

    if not isinstance(generated_at, str) or not generated_at:
        raise ValueError(
            "Manifest does not contain a valid 'generated_at'."
        )

    return generated_at[:10]


def parse_export_file(
    dataset: str,
    data: dict[str, Any],
) -> ExportFile:
    return ExportFile(
        dataset=dataset,
        filename=str(data["filename"]),
        url=str(data["url"]),
        size=int(data["size"]),
        row_count=int(data["row_count"]),
    )


def collect_dataset_files(
    manifest: dict[str, Any],
    selected_datasets: tuple[str, ...],
) -> list[ExportFile]:
    manifest_entries = manifest.get("files")

    if not isinstance(manifest_entries, list):
        raise ValueError(
            "Manifest does not contain a valid 'files' list."
        )

    entries_by_entity: dict[str, dict[str, Any]] = {}

    for entry in manifest_entries:
        if not isinstance(entry, dict):
            continue

        entity = entry.get("entity")

        if isinstance(entity, str):
            entries_by_entity[entity] = entry

    files: list[ExportFile] = []

    for dataset in selected_datasets:
        export = entries_by_entity.get(dataset)

        if export is None:
            raise ValueError(
                f"Dataset '{dataset}' not found in manifest."
            )

        export_type = export.get("type")

        if export_type == "single":
            files.append(
                parse_export_file(
                    dataset=dataset,
                    data=export,
                )
            )

        elif export_type == "split":
            split_files = export.get("files")

            if not isinstance(split_files, list):
                raise ValueError(
                    f"Split dataset '{dataset}' does not "
                    "contain a valid files list."
                )

            for split_file in split_files:
                if not isinstance(split_file, dict):
                    raise ValueError(
                        f"Dataset '{dataset}' contains "
                        "an invalid split file entry."
                    )

                files.append(
                    parse_export_file(
                        dataset=dataset,
                        data=split_file,
                    )
                )

        else:
            raise ValueError(
                f"Unsupported export type '{export_type}' "
                f"for dataset '{dataset}'."
            )

    return files


def save_manifest(
    manifest: dict[str, Any],
    snapshot_name: str,
) -> Path:
    snapshot_dir = RAW_DATA_DIR / snapshot_name
    snapshot_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = snapshot_dir / "index.json"

    with target.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            manifest,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return target


def get_target_path(
    snapshot_name: str,
    export_file: ExportFile,
) -> Path:
    snapshot_dir = RAW_DATA_DIR / snapshot_name

    if export_file.dataset in {"docs", "texts"}:
        dataset_dir = snapshot_dir / export_file.dataset
        dataset_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return dataset_dir / export_file.filename

    snapshot_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return snapshot_dir / export_file.filename


def is_complete_file(
    path: Path,
    expected_size: int,
) -> bool:
    return (
        path.is_file()
        and path.stat().st_size == expected_size
    )


def download_file(
    export_file: ExportFile,
    snapshot_name: str,
) -> DownloadResult:
    target = get_target_path(
        snapshot_name=snapshot_name,
        export_file=export_file,
    )

    if is_complete_file(
        path=target,
        expected_size=export_file.size,
    ):
        return DownloadResult(
            export_file=export_file,
            status="skipped",
            path=target,
        )

    part_path = Path(f"{target}.part")

    timeout = httpx.Timeout(
        connect=CONNECT_TIMEOUT,
        read=READ_TIMEOUT,
        write=READ_TIMEOUT,
        pool=READ_TIMEOUT,
    )

    last_error = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            if part_path.exists():
                part_path.unlink()

            safe_print(
                f"[GET ] {export_file.dataset:<10} "
                f"{export_file.filename} "
                f"({format_bytes(export_file.size)}) "
                f"attempt={attempt}/{MAX_ATTEMPTS}"
            )

            with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
            ) as client:
                with client.stream(
                    "GET",
                    export_file.url,
                ) as response:
                    response.raise_for_status()

                    with part_path.open("wb") as output:
                        for chunk in response.iter_bytes(
                            chunk_size=CHUNK_SIZE
                        ):
                            if chunk:
                                output.write(chunk)

            actual_size = part_path.stat().st_size

            if actual_size != export_file.size:
                raise ValueError(
                    "Size mismatch: "
                    f"expected={export_file.size}, "
                    f"actual={actual_size}"
                )

            os.replace(
                part_path,
                target,
            )

            safe_print(
                f"[ OK ] {export_file.dataset:<10} "
                f"{export_file.filename}"
            )

            return DownloadResult(
                export_file=export_file,
                status="downloaded",
                path=target,
            )

        except Exception as exc:
            last_error = str(exc)

            safe_print(
                f"[WARN] {export_file.dataset:<10} "
                f"{export_file.filename}: {last_error}"
            )

            if part_path.exists():
                try:
                    part_path.unlink()
                except OSError:
                    pass

            if attempt < MAX_ATTEMPTS:
                time.sleep(attempt * 2)

    return DownloadResult(
        export_file=export_file,
        status="failed",
        path=target,
        message=last_error,
    )


def print_download_plan(
    snapshot_name: str,
    files: list[ExportFile],
    selected_datasets: tuple[str, ...],
) -> None:
    print()
    print("OpenParlData bootstrap download plan")
    print("=" * 72)
    print(f"Snapshot: {snapshot_name}")
    print(f"Target:   {RAW_DATA_DIR / snapshot_name}")
    print()

    total_size = 0
    total_rows = 0

    for dataset in selected_datasets:
        dataset_files = [
            item
            for item in files
            if item.dataset == dataset
        ]

        dataset_size = sum(
            item.size
            for item in dataset_files
        )

        dataset_rows = sum(
            item.row_count
            for item in dataset_files
        )

        total_size += dataset_size
        total_rows += dataset_rows

        print(
            f"{dataset:<15} "
            f"files={len(dataset_files):>4}  "
            f"size={format_bytes(dataset_size):>10}  "
            f"rows={dataset_rows:>12,}"
        )

    print("-" * 72)
    print(f"Files: {len(files):,}")
    print(f"Size:  {format_bytes(total_size)}")
    print(f"Rows:  {total_rows:,}")
    print()
    print("DRY RUN ONLY - no export files were downloaded.")


def run_downloads(
    files: list[ExportFile],
    snapshot_name: str,
    workers: int,
) -> list[DownloadResult]:
    total_bytes = sum(
        export_file.size
        for export_file in files
    )

    progress = DownloadProgress(
        total_files=len(files),
        total_bytes=total_bytes,
    )

    results: list[DownloadResult] = []

    safe_print("")
    safe_print(
        f"Starting bootstrap check/download with "
        f"{workers} parallel workers..."
    )
    safe_print(
        f"Expected: {len(files)} files / "
        f"{format_bytes(total_bytes)}"
    )
    safe_print("")

    with ThreadPoolExecutor(
        max_workers=workers,
    ) as executor:
        futures = {
            executor.submit(
                download_file,
                export_file,
                snapshot_name,
            ): export_file
            for export_file in files
        }

        for future in as_completed(futures):
            export_file = futures[future]

            try:
                result = future.result()

            except Exception as exc:
                result = DownloadResult(
                    export_file=export_file,
                    status="failed",
                    path=get_target_path(
                        snapshot_name,
                        export_file,
                    ),
                    message=str(exc),
                )

            results.append(result)
            progress.add_result(result)

    return results


def print_final_summary(
    results: list[DownloadResult],
) -> None:
    downloaded = [
        result
        for result in results
        if result.status == "downloaded"
    ]

    skipped = [
        result
        for result in results
        if result.status == "skipped"
    ]

    failed = [
        result
        for result in results
        if result.status == "failed"
    ]

    verified_size = sum(
        result.export_file.size
        for result in results
        if result.status in {"downloaded", "skipped"}
    )

    verified_rows = sum(
        result.export_file.row_count
        for result in results
        if result.status in {"downloaded", "skipped"}
    )

    print()
    print("=" * 72)
    print("Bootstrap download summary")
    print("=" * 72)
    print(f"Downloaded:    {len(downloaded):,}")
    print(f"Skipped:       {len(skipped):,}")
    print(f"Failed:        {len(failed):,}")
    print(f"Verified size: {format_bytes(verified_size)}")
    print(f"Expected rows: {verified_rows:,}")

    if failed:
        print()
        print("FAILED FILES:")

        for result in failed:
            print(
                f"- {result.export_file.dataset}/"
                f"{result.export_file.filename}: "
                f"{result.message}"
            )

        print()
        print(
            "Bootstrap download is NOT complete. "
            "Run the same command again."
        )

        return

    print()
    print(
        "All requested export files are present "
        "and match the manifest byte sizes."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download and verify OpenParlData bulk exports "
            "for the initial bootstrap."
        )
    )

    parser.add_argument(
        "--datasets",
        nargs="+",
        default=list(DEFAULT_DATASETS),
        help="Datasets to include in the bootstrap.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Show the download plan without "
            "downloading export files."
        ),
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=(
            "Number of parallel downloads. "
            f"Default: {DEFAULT_WORKERS}"
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.workers < 1:
        raise ValueError(
            "--workers must be at least 1."
        )

    selected_datasets = tuple(args.datasets)

    manifest = fetch_manifest()

    snapshot_name = get_snapshot_name(
        manifest
    )

    manifest_path = save_manifest(
        manifest=manifest,
        snapshot_name=snapshot_name,
    )

    files = collect_dataset_files(
        manifest=manifest,
        selected_datasets=selected_datasets,
    )

    print(f"Manifest saved: {manifest_path}")

    if args.dry_run:
        print_download_plan(
            snapshot_name=snapshot_name,
            files=files,
            selected_datasets=selected_datasets,
        )
        return

    results = run_downloads(
        files=files,
        snapshot_name=snapshot_name,
        workers=args.workers,
    )

    print_final_summary(results)

    if any(
        result.status == "failed"
        for result in results
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()