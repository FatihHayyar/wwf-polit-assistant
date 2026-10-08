from __future__ import annotations

import hmac
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import settings
from app.db.database import engine


router = APIRouter(
    prefix="/api/v1/sync",
    tags=["Sync"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOGS_DIR = PROJECT_ROOT / "logs"
STARTUP_TIMEOUT_SECONDS = 10


class DatasetSyncStatus(BaseModel):
    dataset: str
    last_updated_at: datetime | None
    last_id: int | None
    last_run_at: datetime | None
    status: str
    records_processed: int
    records_new: int
    records_changed: int
    records_unchanged: int
    records_error: int
    error_message: str | None


class SyncStatusResponse(BaseModel):
    datasets: list[DatasetSyncStatus]


class SyncRunResponse(BaseModel):
    message: str
    process_id: int
    run_id: str


class DatasetTotals(BaseModel):
    total: int
    successful: int
    failed: int


class RecordTotals(BaseModel):
    new: int
    changed: int
    unchanged: int
    errors: int


class NotificationTotals(BaseModel):
    emails_sent: int
    emails_failed: int


class SyncSummaryResponse(BaseModel):
    run_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_seconds: float | None
    datasets: DatasetTotals
    records: RecordTotals
    notifications: NotificationTotals
    error_message: str | None


class SyncLogResponse(BaseModel):
    run_id: str
    log: str


def verify_sync_api_key(
    x_sync_api_key: str | None,
) -> None:
    configured_key = settings.sync_api_key

    if not configured_key:
        raise HTTPException(
            status_code=503,
            detail="Sync API key is not configured.",
        )

    if not x_sync_api_key or not hmac.compare_digest(
        x_sync_api_key,
        configured_key,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid sync API key.",
        )


def load_run_result(run_id: str) -> dict[str, Any]:
    result_file = LOGS_DIR / f"sync_{run_id}.json"

    if not result_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Sync result not found.",
        )

    try:
        return json.loads(
            result_file.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not read sync result.",
        ) from exc


@router.get(
    "/status",
    response_model=SyncStatusResponse,
)
def get_sync_status() -> SyncStatusResponse:
    query = text(
        """
        SELECT
            dataset,
            last_updated_at,
            last_id,
            last_run_at,
            status,
            records_processed,
            records_new,
            records_changed,
            records_unchanged,
            records_error,
            error_message
        FROM sync_checkpoints
        ORDER BY dataset
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    return SyncStatusResponse(
        datasets=[
            DatasetSyncStatus(**dict(row))
            for row in rows
        ]
    )


@router.get(
    "/latest",
    response_model=SyncSummaryResponse,
)
def get_latest_sync(
    x_sync_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    verify_sync_api_key(x_sync_api_key)

    result_files = list(LOGS_DIR.glob("sync_*.json"))

    if not result_files:
        raise HTTPException(
            status_code=404,
            detail="No sync results found.",
        )

    latest_file = max(
        result_files,
        key=lambda path: path.stat().st_mtime,
    )

    run_id = latest_file.stem.removeprefix("sync_")

    return load_run_result(run_id)


@router.get(
    "/runs/{run_id}/log",
    response_model=SyncLogResponse,
)
def get_sync_run_log(
    run_id: uuid.UUID,
    x_sync_api_key: str | None = Header(default=None),
) -> SyncLogResponse:
    verify_sync_api_key(x_sync_api_key)

    log_file = LOGS_DIR / f"sync_{run_id.hex}.log"

    if not log_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Sync log not found.",
        )

    return SyncLogResponse(
        run_id=run_id.hex,
        log=log_file.read_text(
            encoding="utf-8",
            errors="replace",
        ),
    )


@router.get(
    "/runs/{run_id}",
    response_model=SyncSummaryResponse,
)
def get_sync_run(
    run_id: uuid.UUID,
    x_sync_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    verify_sync_api_key(x_sync_api_key)

    return load_run_result(run_id.hex)


@router.post(
    "/run",
    response_model=SyncRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_sync(
    x_sync_api_key: str | None = Header(default=None),
) -> SyncRunResponse:
    verify_sync_api_key(x_sync_api_key)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    run_id = uuid.uuid4().hex

    ready_file = LOGS_DIR / f"sync_ready_{run_id}.txt"
    log_file = LOGS_DIR / f"sync_{run_id}.log"
    result_file = LOGS_DIR / f"sync_{run_id}.json"

    environment = os.environ.copy()
    environment["SYNC_READY_FILE"] = str(ready_file)
    environment["SYNC_RUN_ID"] = run_id
    environment["SYNC_RESULT_FILE"] = str(result_file)

    try:
        with log_file.open("w", encoding="utf-8") as output:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-u",
                    "-m",
                    "scripts.sync.run_all",
                ],
                cwd=str(PROJECT_ROOT),
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
            )
    except OSError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not start sync process.",
        ) from exc

    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    startup_result = None

    while time.monotonic() < deadline:
        if ready_file.exists():
            try:
                startup_result = ready_file.read_text(
                    encoding="utf-8"
                ).strip()
            except OSError:
                startup_result = None

            if startup_result in {"ACQUIRED", "BUSY"}:
                break

        if process.poll() is not None:
            break

        time.sleep(0.1)

    try:
        ready_file.unlink(missing_ok=True)
    except OSError:
        pass

    if startup_result == "BUSY":
        raise HTTPException(
            status_code=409,
            detail="Another sync is already running.",
        )

    if startup_result != "ACQUIRED":
        raise HTTPException(
            status_code=503,
            detail="Sync startup could not be confirmed. Check sync logs.",
        )

    return SyncRunResponse(
        message="Sync started.",
        process_id=process.pid,
        run_id=run_id,
    )