import json
from pathlib import Path
import tempfile
import unittest
import os
from unittest.mock import patch

from app.core.file_io import atomic_write_json


class AtomicStatusTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows sharing semantics")
    def test_real_windows_reader_lock_is_retried(self):
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        create_file = kernel.CreateFileW
        create_file.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create_file.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "events.json"
            target.write_text('{"position": 500}', encoding="utf-8")
            handle = create_file(str(target), 0x80000000, 1, None, 3, 0, None)
            self.assertNotEqual(handle, ctypes.c_void_p(-1).value)
            closed = False

            def release_reader(_delay):
                nonlocal closed
                if not closed:
                    self.assertTrue(kernel.CloseHandle(handle))
                    closed = True

            try:
                with patch("app.core.file_io.time.sleep", side_effect=release_reader) as sleep:
                    atomic_write_json(target, {"position": 1000})
                self.assertEqual(sleep.call_count, 1)
                self.assertEqual(json.loads(target.read_text()), {"position": 1000})
            finally:
                if not closed:
                    kernel.CloseHandle(handle)

    def test_temporary_windows_lock_retries_without_losing_checkpoint(self):
        original_replace = Path.replace
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "events.json"
            target.write_text('{"position": 500}', encoding="utf-8")
            calls = []

            def locked_then_available(source, destination):
                calls.append(source)
                if len(calls) < 3:
                    self.assertEqual(json.loads(target.read_text()), {"position": 500})
                    raise PermissionError(13, "Windows sharing violation")
                return original_replace(source, destination)

            with patch.object(Path, "replace", locked_then_available), patch("app.core.file_io.time.sleep") as sleep:
                atomic_write_json(target, {"position": 1000})
            self.assertEqual(json.loads(target.read_text()), {"position": 1000})
            self.assertEqual(sleep.call_count, 2)
            self.assertEqual(len(set(calls)), 1)
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])

    def test_permanent_lock_raises_and_preserves_previous_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "events.json"
            target.write_text('{"position": 500}', encoding="utf-8")
            with patch.object(Path, "replace", side_effect=PermissionError(13, "locked")) as replace, patch("app.core.file_io.time.sleep"):
                with self.assertRaises(PermissionError):
                    atomic_write_json(target, {"position": 1000})
            self.assertEqual(replace.call_count, 30)
            self.assertEqual(json.loads(target.read_text()), {"position": 500})
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])

    def test_unrelated_io_failure_is_not_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "events.json"
            with patch.object(Path, "replace", side_effect=OSError(28, "disk full")), patch("app.core.file_io.time.sleep") as sleep:
                with self.assertRaises(OSError):
                    atomic_write_json(target, {})
            sleep.assert_not_called()
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])
