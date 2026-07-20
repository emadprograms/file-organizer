from typing import Any
import os
import pytest
import logging
import yaml
from pathlib import Path
from src.core.config import record_successful_call, TRACKING_DIR, LOG_FILE, AppConfig
from src.core.exceptions import ConfigurationError

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

def test_app_config_load_success(tmp_path: Path) -> None:
    """Test successful configuration loading and directory creation."""
    yaml_file = tmp_path / "config.yaml"
    inbox_dir = tmp_path / "inbox"
    areas_dir = tmp_path / "areas"
    
    config_data = {
        "inbox_path": str(inbox_dir),
        "areas_root_path": str(areas_dir),
        "area_mappings": {"Tenant A": "123"}
    }
    
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
        
    config = AppConfig.load(yaml_file)
    
    assert config.inbox_path == str(inbox_dir)
    assert config.areas_root_path == str(areas_dir)
    assert config.area_mappings == {"Tenant A": "123"}
    assert inbox_dir.exists()
    assert areas_dir.exists()

def test_app_config_load_malformed_yaml(tmp_path: Path) -> None:
    """Test configuration loading with malformed YAML."""
    yaml_file = tmp_path / "config.yaml"
    
    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write("[unclosed list\n")
        
    with pytest.raises(ConfigurationError, match="Malformed YAML"):
        AppConfig.load(yaml_file)

def test_app_config_load_invalid_data(tmp_path: Path) -> None:
    """Test configuration loading with invalid data schema."""
    yaml_file = tmp_path / "config.yaml"
    
    config_data = {
        "inbox_path": "/some/path"
        # missing areas_root_path
    }
    
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
        
    with pytest.raises(ConfigurationError, match="Invalid configuration data"):
        AppConfig.load(yaml_file)

def test_app_config_load_missing_file(tmp_path: Path) -> None:
    """Test configuration loading with missing file."""
    yaml_file = tmp_path / "missing_config.yaml"
    
    with pytest.raises(ConfigurationError, match="Configuration file not found"):
        AppConfig.load(yaml_file)
