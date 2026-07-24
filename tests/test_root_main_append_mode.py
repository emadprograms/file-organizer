import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.main import run_append_mode
from src.watcher.lock import LockExistsError

def test_run_append_mode_success(caplog, tmp_path):
    caplog.set_level("INFO")
    config = MagicMock()
    config.inbox_path = str(tmp_path)
    
    with patch("src.watcher.lock.acquire_lock") as mock_acquire, \
         patch("src.watcher.lock.release_lock") as mock_release, \
         patch("src.main.setup_logging"), \
         patch("src.watcher.orchestrator.FSUIOrchestrator") as mock_orchestrator:
         
        mock_orch_instance = MagicMock()
        mock_orchestrator.return_value = mock_orch_instance
        
        run_append_mode(config)
        
        import hashlib
        inbox_hash = hashlib.md5(str(tmp_path.resolve()).encode()).hexdigest()
        lock_dir = Path.home() / ".file-organizer" / "locks"
        mock_acquire.assert_called_once_with(lock_dir / f"inbox_{inbox_hash}.lock")
        mock_release.assert_called_once_with(lock_dir / f"inbox_{inbox_hash}.lock")
        mock_orch_instance.process_inbox.assert_called_once()
        assert "Listener started..." in caplog.text

def test_run_append_mode_already_locked(caplog, tmp_path):
    config = MagicMock()
    config.inbox_path = str(tmp_path)
    
    with patch("src.watcher.lock.acquire_lock", side_effect=LockExistsError), \
         patch("sys.exit") as mock_exit, \
         patch("src.llm.llm.LLMClient"), \
         patch("src.watcher.orchestrator.FSUIOrchestrator"):
        
        run_append_mode(config)
        
        mock_exit.assert_called_once_with(0)
        assert "Listener is already running" in caplog.text
