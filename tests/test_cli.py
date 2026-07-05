import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch
from src.organize import get_parser, validate_environment, main

def test_parser_default_model():
    parser = get_parser()
    args = parser.parse_args(["./pdfs/1273"])
    assert args.target_dir == Path("./pdfs/1273")
    assert args.model == "gemma-4-26b-a4b-it"

def test_parser_custom_model():
    parser = get_parser()
    args = parser.parse_args(["./pdfs/1273", "--model", "gemma-4-31b-it"])
    assert args.model == "gemma-4-31b-it"

@patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True)
def test_validate_environment_success():
    # Should not exit
    validate_environment()

@patch("src.organize.load_dotenv")
@patch.dict(os.environ, {}, clear=True)
def test_validate_environment_missing_key(mock_load_dotenv, capsys):
    with pytest.raises(SystemExit) as exc_info:
        validate_environment()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "ERROR: GEMINI_API_KEY is missing from the environment." in captured.err

@patch("src.processing.organizer.FileOrganizer")
@patch("src.processing.pipeline.Pipeline")
@patch("src.organize.process_cleaning_phase")
@patch("src.organize.LLMClient")
@patch("src.organize.setup_logging")
@patch("src.organize.validate_target_directory")
@patch("src.organize.validate_environment")
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True)
@patch("sys.argv", ["organize.py", "./pdfs/1273"])
def test_main_success(mock_validate_env, mock_validate_target, mock_setup_logging, mock_llm_client, mock_process_cleaning, mock_pipeline, mock_organizer):
    mock_validate_target.return_value = "1273"
    mock_setup_logging.return_value = "/tmp/logs"
    mock_process_cleaning.return_value = []
    
    mock_pipeline_inst = mock_pipeline.return_value
    mock_pipeline_inst._group_pages_into_documents.return_value = []
    
    mock_organizer_inst = mock_organizer.return_value
    mock_organizer_inst.organize.return_value = []
    
    # We also need to mock Path.glob because args.target_dir.glob is called
    with patch.object(Path, "glob") as mock_glob, patch("builtins.open"), patch.object(Path, "replace"), patch("src.organize.fitz") as mock_fitz:
        mock_glob.return_value = [Path("1273.pdf")]
        mock_fitz.open.return_value.page_count = 0
        assert main() == 0
        
    mock_validate_env.assert_called_once()
    mock_validate_target.assert_called_once_with(Path("./pdfs/1273"))
    mock_setup_logging.assert_called_once()
    mock_llm_client.assert_called_once()
    mock_pipeline.assert_called_once_with(api_key="test_key")
    mock_organizer_inst.organize.assert_called_once()

def test_validate_target_directory_success(tmp_path):
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    (target_dir / "1273_categorized.pdf").touch()
    (target_dir / "1273_report.json").touch()
    
    from src.organize import validate_target_directory
    house_id = validate_target_directory(target_dir)
    assert house_id == "1273"
    assert (target_dir / "output").exists()
    assert (target_dir / "output").is_dir()

def test_validate_target_directory_missing_pdf(tmp_path, capsys):
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    (target_dir / "1273_report.json").touch()
    
    from src.organize import validate_target_directory
    with pytest.raises(SystemExit) as exc_info:
        validate_target_directory(target_dir)
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "ERROR: No *_categorized.pdf found" in captured.err

def test_validate_target_directory_mismatch_id(tmp_path, capsys):
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    (target_dir / "1273_categorized.pdf").touch()
    (target_dir / "1274_report.json").touch()
    
    from src.organize import validate_target_directory
    with pytest.raises(SystemExit) as exc_info:
        validate_target_directory(target_dir)
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "ERROR: ID mismatch between PDF (1273) and JSON (1274)" in captured.err
