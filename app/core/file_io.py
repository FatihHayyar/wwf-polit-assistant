"""Atomic status-file writes that tolerate brief Windows sharing violations."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import time


def atomic_write_json(path: Path, value, *, indent: int | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        # Independent writers must never share a fixed .tmp filename.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, indent=indent)
            handle.flush()
            os.fsync(handle.fileno())
        # Readers and antivirus scanners may temporarily deny replacement on Windows.
        # Keep the old valid checkpoint intact and retry the same completed file.
        for attempt in range(30):
            try:
                temporary.replace(path)
                return
            except PermissionError:
                if attempt == 29:
                    raise
                time.sleep(min(0.05 * (attempt + 1), 0.5))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
