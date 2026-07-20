import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.main import run_append_mode
from src.fs_ui.lock import LockExistsError

def test_run_append_mode_success(caplog, tmp_path):
    caplog.set_level("INFO")
    config = MagicMock()
    config.inbox_path = str(tmp_path)
    
    with patch("src.fs_ui.lock.acquire_lock") as mock_acquire, \
         patch("src.fs_ui.lock.release_lock") as mock_release, \
         patch("src.llm.llm.LLMClient"), \
         patch("src.fs_ui.orchestrator.FSUIOrchestrator") as mock_orchestrator:
         
        mock_orch_instance = MagicMock()
        mock_orchestrator.return_value = mock_orch_instance
        
        run_append_mode(config)
        
        mock_acquire.assert_called_once_with(tmp_path / ".inbox.lock")
        mock_release.assert_called_once_with(tmp_path / ".inbox.lock")
        mock_orch_instance.process_inbox.assert_called_once()
        assert "Listener started..." in caplog.text

def test_run_append_mode_already_locked(caplog, tmp_path):
    config = MagicMock()
    config.inbox_path = str(tmp_path)
    
    with patch("src.fs_ui.lock.acquire_lock", side_effect=LockExistsError), \
         patch("sys.exit") as mock_exit, \
         patch("src.llm.llm.LLMClient"), \
         patch("src.fs_ui.orchestrator.FSUIOrchestrator"):
        
        run_append_mode(config)
        
        mock_exit.assert_called_once_with(0)
        assert "Listener is already running" in caplog.text
