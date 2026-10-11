import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.api.routes import sync
from scripts.sync import run_all

class SyncControlTests(unittest.TestCase):
    def test_cancel_protects_api_and_only_signals_supported_running_worker(self):
        import uuid, json
        run_id=uuid.uuid4()
        with tempfile.TemporaryDirectory() as folder, patch.object(sync, 'LOGS_DIR', Path(folder)), patch.object(sync, 'verify_sync_api_key') as verify:
            path=Path(folder)/f'sync_{run_id.hex}.json'
            path.write_text(json.dumps({'status':'running','cancellable':True}))
            result=sync.cancel_sync(run_id,'test-key')
            verify.assert_called_once_with('test-key')
            self.assertEqual(result['run_id'],run_id.hex)
            self.assertTrue(path.with_suffix('.cancel').exists())
            path.write_text(json.dumps({'status':'running'}))
            with self.assertRaises(HTTPException) as raised:sync.cancel_sync(run_id,'test-key')
            self.assertEqual(raised.exception.status_code,409)
    def test_cancel_terminates_active_child(self):
        child=MagicMock(); child.poll.return_value=None
        with patch.object(run_all,'check_cancelled',side_effect=[None,run_all.SyncCancelled('stop')]), patch.object(run_all.subprocess,'Popen',return_value=child):
            with self.assertRaises(run_all.SyncCancelled):run_all.run_dataset('dummy.module')
            child.terminate.assert_called_once()
            child.wait.assert_called_once_with(timeout=10)
    def test_cancel_does_not_start_next_dataset(self):
        with patch.object(run_all,'check_cancelled',side_effect=run_all.SyncCancelled('stop')), patch.object(run_all.subprocess,'Popen') as start:
            with self.assertRaises(run_all.SyncCancelled):run_all.run_dataset('dummy.module')
            start.assert_not_called()

    def test_resume_skips_completed_stage_and_retries_failed_stage(self):
        with patch("scripts.sync.source_batches.job_directory", return_value=None), patch.object(run_all, "RESUME_FILE", None):
            result=run_all.initial_result()
        result["dataset_results"]={"Affairs":{"status":"completed","records":{"new":2}},"Agendas":{"status":"failed"}}
        with patch.object(run_all,"SYNC_MODULES",[("Affairs","affairs.module"),("Agendas","agendas.module")]), patch.object(run_all,"run_dataset",return_value=0) as start, patch.object(run_all,"check_cancelled"), patch.object(run_all,"save_result"), patch.object(run_all,"checkpoint_snapshot",return_value={"agendas":{"new":3}}):
            run_all.run_all_syncs(result)
            start.assert_called_once_with("agendas.module")
        self.assertEqual(result["datasets"]["successful"],2)
        self.assertEqual(result["datasets"]["failed"],0)
        self.assertEqual(result["records"]["new"],5)

if __name__=='__main__':unittest.main()
