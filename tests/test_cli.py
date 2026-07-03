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

@patch("src.organize.validate_environment")
@patch("sys.argv", ["organize.py", "./pdfs/1273"])
def test_main_success(mock_validate):
    # Until task 03-02, main just validates env and returns 0
    assert main() == 0
    mock_validate.assert_called_once()
