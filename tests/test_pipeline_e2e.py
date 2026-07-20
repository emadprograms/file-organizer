from typing import Any
"""End-to-end tests for the pipeline.

Uses isolated fixture files in tests/fixtures/golden_1273/ to avoid
relying on live API calls or the main pdfs/ directory.
Mocked LLM responses are loaded from tests/fixtures/golden_1273/state/.
"""

import os
import json
import shutil
import sys
from pathlib import Path

import pytest
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "golden_1273"
STATE_DIR = FIXTURES_DIR / "state"

def _setup_run_dir(tmp_path: Path) -> Path:
    house_dir = tmp_path / "1273"
    house_dir.mkdir()

    # Copy minimal fixture PDF
    shutil.copy(FIXTURES_DIR / "input" / "1273" / "1273_categorized.pdf", house_dir / "1273_categorized.pdf")

    # Copy report
    shutil.copy(FIXTURES_DIR / "input" / "1273" / "1273_report.json", house_dir / "1273_report.json")
    
    # Copy source files
    source_dir = house_dir / ".source_files"
    source_dir.mkdir()
    shutil.copy(FIXTURES_DIR / "input" / "1273" / ".source_files" / "1273_tenants.yaml", source_dir / "1273_tenants.yaml")

    return house_dir

@patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
@patch("src.main.process_unclassified_pdf")
@patch("src.timeline.phase.canonicalize_with_llm")
@patch("src.grouping.process_with_shrink")
@patch("src.routing.route_document")
def test_dry_run_end_to_end(mock_route, mock_shrink, mock_canonicalize, mock_process_unclass, tmp_path, capfd) -> None:
    """
    Test dry run end to end.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    house_dir = _setup_run_dir(tmp_path)
    output_dir = house_dir / "output"
    
    with open(STATE_DIR / "1273_1_cleaned.json", "r", encoding="utf-8") as f:
        cleaned_data = json.load(f)
    mock_canonicalize.return_value = {"Ahmed Ali": "يونس محمد مالك"}
    
    from src.core.schemas import DocumentGroup
    with open(STATE_DIR / "1273_2_grouped.json", "r", encoding="utf-8") as f:
        grouped_data = json.load(f)
    mock_shrink.return_value = [DocumentGroup(**d) for d in grouped_data]
    
    mock_route.return_value = ("05_عقود", True)
    
    config_path = tmp_path / "config.yaml"
    config_path.write_text(f"inbox_path: {tmp_path}/inbox\nareas_root_path: {tmp_path}\narea_mappings: {{}}", encoding="utf-8")
    os.environ["FILE_ORGANIZER_CONFIG"] = str(config_path)
    
    test_args = ["main.py", "create", str(house_dir), "--output-dir", str(output_dir), "--dry-run", "--verbose", "--skip-llm"]
    
    with patch.object(sys, 'argv', test_args):
        from src.main import main
        exit_code = main()
        assert exit_code == 0
        
    out, err = capfd.readouterr()
    combined_output = out + err
    
    assert "1273" in combined_output
    assert "Ahmed" in combined_output or "يونس" in combined_output
    
    output_pdf_dir = output_dir / "1273 - يونس محمد مالك"
    assert not output_pdf_dir.exists()

@patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
@patch("src.main.process_unclassified_pdf")
@patch("src.timeline.phase.canonicalize_with_llm")
@patch("src.grouping.process_with_shrink")
@patch("src.routing.route_document")
def test_full_run_end_to_end(mock_route, mock_shrink, mock_canonicalize, mock_process_unclass, tmp_path) -> None:
    """
    Test full run end to end.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    house_dir = _setup_run_dir(tmp_path)
    output_dir = house_dir / "output"
    
    with open(STATE_DIR / "1273_1_cleaned.json", "r", encoding="utf-8") as f:
        cleaned_data = json.load(f)
    mock_canonicalize.return_value = {"Ahmed Ali": "يونس محمد مالك"}
    
    from src.core.schemas import DocumentGroup
    with open(STATE_DIR / "1273_2_grouped.json", "r", encoding="utf-8") as f:
        grouped_data = json.load(f)
    mock_shrink.return_value = [DocumentGroup(**d) for d in grouped_data]
    
    mock_route.return_value = ("05_عقود", True)
    
    config_path = tmp_path / "config.yaml"
    config_path.write_text(f"inbox_path: {tmp_path}/inbox\nareas_root_path: {tmp_path}\narea_mappings: {{}}", encoding="utf-8")
    os.environ["FILE_ORGANIZER_CONFIG"] = str(config_path)
    
    test_args = ["main.py", "create", str(house_dir), "--output-dir", str(output_dir), "--verbose", "--skip-llm"]
    
    with patch.object(sys, 'argv', test_args):
        from src.main import main
        exit_code = main()
        assert exit_code == 0
        
    # Check the final output from the reconciliation report generated in source files
    report_path = output_dir / ".source_files" / "1273_3_routed_and_finalized.json"
    assert report_path.exists()
    
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
        
    # Find the output path for the page
    output_path = report["per_page"][0]["output_file"]
    assert "1273 - يونس محمد مالك" in output_path
    assert "يونس محمد مالك ‎(2000 - الآن)‎/05_عقود" in output_path
