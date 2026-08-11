import pytest
from pathlib import Path
from src.main import validate_target_directory
from src.core.exceptions import ValidationError

def test_validate_target_directory_extracts_correct_ids(tmp_path: Path):
    """
    Ensure validate_target_directory strictly extracts the correct, deduped IDs,
    completely ignoring backup files and correctly parsing different filename patterns.
    """
    # Create required .pdf file so validation passes
    (tmp_path / "dummy.pdf").touch()

    # Create dummy json files
    (tmp_path / "568_report.json").touch()
    (tmp_path / "568_report_old.json").touch()  # Should be ignored
    (tmp_path / "568 - محمد عمران محمد أسلم_report.json").touch()
    (tmp_path / "999_report_old.json").touch() # Should be ignored
    
    # .raw_dump.json is also a valid pattern
    (tmp_path / "123.raw_dump.json").touch()
    
    ids = validate_target_directory(tmp_path)
    
    # Deduped and correctly parsed IDs
    # Expected: "568", "568 - محمد عمران محمد أسلم", "123"
    assert "568" in ids
    assert "568 - محمد عمران محمد أسلم" in ids
    assert "123" in ids
    assert len(ids) == 3

def test_validate_target_directory_source_files_directory(tmp_path: Path):
    """
    Test extraction of IDs from .source_files subdirectory.
    """
    (tmp_path / "dummy.pdf").touch()
    source_files = tmp_path / ".source_files"
    source_files.mkdir()
    
    (source_files / "777_report.json").touch()
    (source_files / "888_report_old.json").touch() # Should be ignored
    
    ids = validate_target_directory(tmp_path)
    
    assert "777" in ids
    assert len(ids) == 1

def test_validate_target_directory_empty_raises_error(tmp_path: Path):
    """
    Test that an empty directory raises ValidationError.
    """
    with pytest.raises(ValidationError, match="No .raw_dump.json or _report.json found"):
        validate_target_directory(tmp_path)
