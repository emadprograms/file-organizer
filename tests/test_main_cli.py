from typing import Any
import os
import sys
import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

logger = logging.getLogger(f"file_organizer.{__name__}")

from src.main import get_parser, validate_environment, main
from src.core.exceptions import ConfigurationError, ValidationError

def test_parser_default_model() -> None:
    """
    Test parser default model.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    parser = get_parser()
    args = parser.parse_args(["create", "./pdfs/1273"])
    assert args.command == "create"
    assert args.target_dir == Path("./pdfs/1273")
    assert args.model == "gemma-4-31b-it"

def test_parser_custom_model() -> None:
    """
    Test parser custom model.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    parser = get_parser()
    args = parser.parse_args(["create", "./pdfs/1273", "--model", "gemma-4-31b-it"])
    assert args.model == "gemma-4-31b-it"

def test_parser_flags() -> None:
    """
    Test parser flags.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    parser = get_parser()
    args = parser.parse_args(["create", "./pdfs/1273", "--verbose", "--skip-llm"])
    assert args.verbose is True
    assert args.skip_llm is True

@patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True)
def test_validate_environment_success() -> None:
    """
    Test validate environment success.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    # Should not exit
    validate_environment()

@patch("src.main.load_dotenv")
@patch.dict(os.environ, {}, clear=True)
def test_validate_environment_missing_key(mock_load_dotenv, capsys) -> None:
    """
    Test validate environment missing key.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    with pytest.raises(ConfigurationError) as exc_info:
        validate_environment()
    assert "GEMINI_API_KEY is missing" in str(exc_info.value)

@patch("src.main.process_unclassified_pdf")
@patch("src.timeline.FileOrganizer")
@patch("src.pipeline.pipeline.Pipeline")
@patch("src.main.LLMClient")
@patch("src.main.setup_logging")
@patch("src.main.validate_target_directory")
@patch("src.main.validate_environment")
@patch("src.core.config.AppConfig.load")
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True)
@patch("sys.argv", ["main.py", "create", "./pdfs/1273"])
def test_main_success(mock_app_config_load, mock_validate_env, mock_validate_target, mock_setup_logging, mock_llm_client, mock_pipeline, mock_organizer, mock_process_unclass) -> None:
    """
    Test main success.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    mock_config = MagicMock()
    mock_config.areas_root_path = str(Path("./pdfs").resolve())
    mock_app_config_load.return_value = mock_config
    mock_validate_target.return_value = ["1273"]
    mock_setup_logging.return_value = "/tmp/logs"
    
    mock_pipeline_inst = mock_pipeline.return_value
    mock_pipeline_inst._clean_documents.return_value = ([], None)
    mock_pipeline_inst._group_documents.return_value = []
    mock_pipeline_inst._route_documents.return_value = []
    
    mock_organizer_inst = mock_organizer.return_value
    mock_organizer_inst.organize.return_value = ([], "1273")
    
    def custom_glob(self, pattern) -> Any:
        """
        Provide the custom glob fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        if "categorized" in pattern:
            return [Path("1273_categorized.pdf")]
        elif "json" in pattern:
            return [Path("1273_report.json")]
        return [Path("1273.pdf")]
        
    from unittest.mock import mock_open
    with patch.object(Path, "glob", autospec=True) as mock_glob, patch.object(Path, "exists", return_value=False), patch("builtins.open", mock_open(read_data="{}")), patch.object(Path, "replace"), patch("os.replace"), patch("src.main.fitz") as mock_fitz, patch("src.main.json.load") as mock_json_load, patch("shutil.move"), patch("yaml.safe_load") as mock_yaml_load:
        mock_glob.side_effect = custom_glob
        mock_fitz.open.return_value.__enter__.return_value.page_count = 0
        mock_json_load.return_value = []
        mock_yaml_load.return_value = {}
        assert main() == 0
        
    mock_validate_env.assert_called_once()
    assert mock_validate_target.call_count == 2
    mock_setup_logging.assert_called_once()
    mock_llm_client.assert_called_once()
    assert mock_pipeline.call_count == 3
    from unittest.mock import call
    mock_pipeline.assert_has_calls([
        call(api_key="test_key"),
        call(api_key="test_key"),
        call(api_key="test_key", routing_model=None)
    ], any_order=True)
    mock_organizer_inst.organize.assert_called_once()

def test_validate_target_directory_success(tmp_path) -> None:
    """
    Test validate target directory success.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    (target_dir / "1273_categorized.pdf").touch()
    (target_dir / "1273_report.json").touch()
    
    from src.main import validate_target_directory
    house_ids = validate_target_directory(target_dir)
    assert house_ids == ["1273"]

def test_validate_target_directory_missing_pdf(tmp_path, capsys) -> None:
    """
    Test validate target directory missing pdf.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    (target_dir / "1273_report.json").touch()
    
    from src.main import validate_target_directory
    with pytest.raises(ValidationError) as exc_info:
        validate_target_directory(target_dir)
    assert "No *_categorized.pdf found" in str(exc_info.value)

def test_validate_target_directory_mismatch_id(tmp_path, capsys) -> None:
    """
    Test validate target directory mismatch id.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    (target_dir / "1273_categorized.pdf").touch()
    (target_dir / "1274_report.json").touch()
    
    from src.main import validate_target_directory
    with pytest.raises(ValidationError) as exc_info:
        validate_target_directory(target_dir)
    assert "No matching PDF and JSON pairs found." in str(exc_info.value)

def test_validate_target_directory_missing_json(tmp_path, capsys) -> None:
    """Missing _report.json is gracefully caught and exits with code 1."""
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    # Provide a PDF but NO matching _report.json
    (target_dir / "1273_categorized.pdf").touch()

    from src.main import validate_target_directory
    with pytest.raises(ValidationError) as exc_info:
        validate_target_directory(target_dir)
    assert "No *_report.json found" in str(exc_info.value)


@patch("src.core.config.AppConfig")
@patch("sys.argv", ["main.py", "create", "/tmp/outside_path"])
def test_main_create_boundary_check(mock_app_config, caplog) -> None:
    """Test that create command rejects paths outside of areas_root_path."""
    mock_app_config.load.return_value.areas_root_path = "/tmp/allowed_root"
    
    with patch("src.core.config.AppConfig.load", return_value=mock_app_config.load.return_value):
        assert main() == 1
    
    assert "is outside the allowed areas root" in caplog.text
