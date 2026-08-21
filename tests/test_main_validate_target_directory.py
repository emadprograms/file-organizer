import pytest
from pypdf import PdfWriter
def make_valid_pdf(path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(path, "wb") as f:
        writer.write(f)

from pathlib import Path
from src.main import validate_target_directory
from src.core.exceptions import ValidationError

def test_validate_target_directory_extracts_correct_ids(tmp_path: Path):
    """
    Ensure validate_target_directory strictly extracts the correct, deduped IDs,
    completely ignoring backup files and correctly parsing different filename patterns.
    """
    # Create required .pdf file so validation passes
    make_valid_pdf(tmp_path / "dummy.pdf")

    # Create dummy json files
    make_valid_pdf(tmp_path / "568_report.json")
    make_valid_pdf(tmp_path / "568_report_old.json")  # Should be ignored
    make_valid_pdf(tmp_path / "568 - محمد عمران محمد أسلم_report.json")
    make_valid_pdf(tmp_path / "999_report_old.json") # Should be ignored
    
    # .raw_dump.json is also a valid pattern
    make_valid_pdf(tmp_path / "123.raw_dump.json")
    
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
    make_valid_pdf(tmp_path / "dummy.pdf")
    source_files = tmp_path / ".source_files"
    source_files.mkdir()
    
    make_valid_pdf(source_files / "777_report.json")
    make_valid_pdf(source_files / "888_report_old.json") # Should be ignored
    
    ids = validate_target_directory(tmp_path)
    
    assert "777" in ids
    assert len(ids) == 1

def test_validate_target_directory_empty_raises_error(tmp_path: Path):
    """
    Test that an empty directory raises ValidationError.
    """
    with pytest.raises(ValidationError, match="No .raw_dump.json or _report.json found"):
        validate_target_directory(tmp_path)
