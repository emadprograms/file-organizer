from typing import Any
import os
import pytest
import logging
from src.core.config import record_successful_call, TRACKING_DIR, LOG_FILE

logger = logging.getLogger(f"file_organizer.{__name__}")

def test_record_successful_call_creates_dir_and_file(tmp_path, monkeypatch) -> None:
    """
    Test record successful call creates dir and file.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    # Mock TRACKING_DIR and LOG_FILE to use tmp_path
    mock_tracking_dir = tmp_path / ".tracking"
    mock_log_file = mock_tracking_dir / "api_calls.log"
    
    monkeypatch.setattr("src.core.config.TRACKING_DIR", mock_tracking_dir)
    monkeypatch.setattr("src.core.config.LOG_FILE", mock_log_file)
    
    # Execution
    record_successful_call()
    
    # Verification
    assert mock_tracking_dir.exists()
    assert mock_log_file.exists()
    with open(mock_log_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        # Should be a timestamp (float)
        assert float(lines[0].strip()) > 0

def test_record_successful_call_appends(tmp_path, monkeypatch) -> None:
    """
    Test record successful call appends.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    mock_tracking_dir = tmp_path / ".tracking"
    mock_log_file = mock_tracking_dir / "api_calls.log"
    
    monkeypatch.setattr("src.core.config.TRACKING_DIR", mock_tracking_dir)
    monkeypatch.setattr("src.core.config.LOG_FILE", mock_log_file)
    
    record_successful_call()
    record_successful_call()
    
    with open(mock_log_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 2

def test_record_successful_call_handles_exception(tmp_path, monkeypatch) -> None:
    """
    Test record successful call handles exception.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    # Create a directory where the log file should be, but make it read-only or similar
    # A simpler way is to mock open to raise an exception
    import builtins
    
    original_open = builtins.open
    def mock_open(*args, **kwargs) -> None:
        """
        Provide the mock open fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        if "api_calls.log" in str(args[0]):
            raise IOError("Mocked write failure")
        return original_open(*args, **kwargs)
    
    monkeypatch.setattr(builtins, "open", mock_open)
    
    # This should not crash the application
    record_successful_call()
