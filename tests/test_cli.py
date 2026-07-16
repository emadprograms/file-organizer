import os
import sys
import pytest
import logging
from pathlib import Path
from unittest.mock import patch

logger = logging.getLogger(f"file_organizer.{__name__}")

from src.main import get_parser, validate_environment, main
from src.core.exceptions import ConfigurationError, ValidationError

def test_parser_default_model():
    parser = get_parser()
    args = parser.parse_args(["./pdfs/1273"])
    assert args.target_dir == Path("./pdfs/1273")
    assert args.model == "gemma-4-31b-it"

def test_parser_custom_model():
    parser = get_parser()
    args = parser.parse_args(["./pdfs/1273", "--model", "gemma-4-31b-it"])
    assert args.model == "gemma-4-31b-it"

def test_parser_flags():
    parser = get_parser()
    args = parser.parse_args(["./pdfs/1273", "--verbose", "--skip-llm"])
    assert args.verbose is True
    assert args.skip_llm is True

@patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True)
def test_validate_environment_success():
    # Should not exit
    validate_environment()

@patch("src.main.load_dotenv")
@patch.dict(os.environ, {}, clear=True)
def test_validate_environment_missing_key(mock_load_dotenv, capsys):
    with pytest.raises(ConfigurationError) as exc_info:
        validate_environment()
    assert "GEMINI_API_KEY is missing" in str(exc_info.value)

@patch("src.timeline.FileOrganizer")
@patch("src.pipeline.pipeline.Pipeline")
@patch("src.main.LLMClient")
@patch("src.main.setup_logging")
@patch("src.main.validate_target_directory")
@patch("src.main.validate_environment")
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True)
@patch("sys.argv", ["main.py", "./pdfs/1273"])
def test_main_success(mock_validate_env, mock_validate_target, mock_setup_logging, mock_llm_client, mock_pipeline, mock_organizer):
    mock_validate_target.return_value = "1273"
    mock_setup_logging.return_value = "/tmp/logs"
    
    mock_pipeline_inst = mock_pipeline.return_value
    mock_pipeline_inst._clean_documents.return_value = ([], None)
    mock_pipeline_inst._group_documents.return_value = []
    mock_pipeline_inst._route_documents.return_value = []
    
    mock_organizer_inst = mock_organizer.return_value
    mock_organizer_inst.organize.return_value = ([], "1273")
    
    def custom_glob(self, pattern):
        if "categorized" in pattern:
            return [Path("1273_categorized.pdf")]
        elif "json" in pattern:
            return [Path("1273_report.json")]
        return [Path("1273.pdf")]
        
    with patch.object(Path, "glob", autospec=True) as mock_glob, patch("builtins.open"), patch.object(Path, "replace"), patch("os.replace"), patch("src.main.fitz") as mock_fitz, patch("src.main.json.load") as mock_json_load, patch("shutil.move"):
        mock_glob.side_effect = custom_glob
        mock_fitz.open.return_value.__enter__.return_value.page_count = 0
        mock_json_load.return_value = []
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

def test_validate_target_directory_success(tmp_path):
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    (target_dir / "1273_categorized.pdf").touch()
    (target_dir / "1273_report.json").touch()
    
    from src.main import validate_target_directory
    house_id = validate_target_directory(target_dir)
    assert house_id == "1273"

def test_validate_target_directory_missing_pdf(tmp_path, capsys):
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    (target_dir / "1273_report.json").touch()
    
    from src.main import validate_target_directory
    with pytest.raises(ValidationError) as exc_info:
        validate_target_directory(target_dir)
    assert "No *_categorized.pdf found" in str(exc_info.value)

def test_validate_target_directory_mismatch_id(tmp_path, capsys):
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    (target_dir / "1273_categorized.pdf").touch()
    (target_dir / "1274_report.json").touch()
    
    from src.main import validate_target_directory
    with pytest.raises(ValidationError) as exc_info:
        validate_target_directory(target_dir)
    assert "ID mismatch" in str(exc_info.value)

def test_validate_target_directory_missing_json(tmp_path, capsys):
    """Missing _report.json is gracefully caught and exits with code 1."""
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    # Provide a PDF but NO matching _report.json
    (target_dir / "1273_categorized.pdf").touch()

    from src.main import validate_target_directory
    with pytest.raises(ValidationError) as exc_info:
        validate_target_directory(target_dir)
    assert "No *_report.json found" in str(exc_info.value)

