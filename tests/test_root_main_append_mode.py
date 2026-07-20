import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.main import run_append_mode
from filelock import FileLock, Timeout

def test_run_append_mode_success(caplog, tmp_path):
    caplog.set_level("INFO")
    config = MagicMock()
    config.inbox_path = str(tmp_path)
    
    with patch("src.main.FileLock") as mock_filelock, patch("src.main.LLMClient"):
        lock_instance = MagicMock()
        mock_filelock.return_value = lock_instance
        
        run_append_mode(config)
        
        mock_filelock.assert_called_once_with(str(tmp_path / ".inbox.lock"), timeout=0)
        lock_instance.__enter__.assert_called_once()
        
        assert "Listener started..." in caplog.text

def test_run_append_mode_already_locked(caplog, tmp_path):
    config = MagicMock()
    config.inbox_path = str(tmp_path)
    
    with patch("src.main.FileLock") as mock_filelock, patch("sys.exit") as mock_exit, patch("src.main.LLMClient"):
        lock_instance = MagicMock()
        lock_instance.__enter__.side_effect = Timeout(str(tmp_path / ".inbox.lock"))
        mock_filelock.return_value = lock_instance
        
        run_append_mode(config)
        
        mock_exit.assert_called_once_with(0)
        assert "Listener is already running" in caplog.text
