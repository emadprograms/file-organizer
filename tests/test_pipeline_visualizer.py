from typing import Any
import pytest
from src.pipeline.visualizer import Visualizer
from src.presentation.ui import set_verbosity

def test_visualizer_print_summary_empty(capsys) -> None:
    """Test that Visualizer handles empty summary and per_page lists gracefully."""
    set_verbosity(True)
    visualizer = Visualizer()
    
    visualizer.print_summary(
        house_id="1273",
        summary={},
        per_page=[],
        documents=[]
    )
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "=== Dry Run Output Preview ===" in output
    assert "Total Output Pages" in output
    assert "1273" in output
    # With no files, it shouldn't have any tenants/categories
    assert "👤" not in output
    assert "📁" not in output


def test_visualizer_print_summary_populated(capsys) -> None:
    """Test that Visualizer correctly builds the tree from a populated per_page manifest."""
    set_verbosity(True)
    visualizer = Visualizer()
    
    summary = {
        "total_output_pages": 5,
        "output_file_count": 2
    }
    
    per_page = [
        {"output_file": "1273/Emad 2020-2023/01_forms/2021-01-01 - Test Form.pdf"},
        {"output_file": "1273/Emad 2020-2023/02_letters/2022-05-01 - Test Letter.pdf"},
        {"output_file": "1273/Emad 2020-2023/01_forms/2021-01-01 - Test Form.pdf"} # duplicate file reference (e.g. multi-page)
    ]
    
    visualizer.print_summary(
        house_id="1273",
        summary=summary,
        per_page=per_page,
        documents=[]
    )
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Assert Table output
    assert "Total Output Pages" in output
    assert "5" in output
    assert "Total Output Files" in output
    assert "2" in output
    
    # Assert Tree output
    assert "1273" in output
    assert "Emad 2020-2023" in output
    assert "01_forms" in output
    assert "02_letters" in output
    assert "2021-01-01 - Test Form.pdf" in output
    assert "2022-05-01 - Test Letter.pdf" in output


def test_visualizer_print_summary_path_normalization(capsys) -> None:
    """Test that Visualizer normalizes Windows backslashes to forward slashes for tree construction."""
    set_verbosity(True)
    visualizer = Visualizer()
    
    per_page = [
        # Windows-style backslashes
        {"output_file": "1273\\John Doe 2019-2021\\04_receipts\\receipt1.pdf"},
        # Unix-style forward slashes
        {"output_file": "1273/John Doe 2019-2021/05_contracts/contract1.pdf"},
        # Mixed slashes
        {"output_file": "1273\\John Doe 2019-2021/04_receipts\\receipt2.pdf"}
    ]
    
    visualizer.print_summary(
        house_id="1273",
        summary={},
        per_page=per_page,
        documents=[]
    )
    
    captured = capsys.readouterr()
    output = captured.out
    
    # The tenant should only be listed once
    assert output.count("John Doe 2019-2021") == 1
    
    # Both categories should be present
    assert "04_receipts" in output
    assert "05_contracts" in output
    
    # All files should be nested correctly
    assert "receipt1.pdf" in output
    assert "receipt2.pdf" in output
    assert "contract1.pdf" in output

from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
from src.core.config import AppConfig

@patch("src.pipeline.visualizer.Visualizer.print_summary")
def test_ingest_dry_run_calls_visualizer(mock_print_summary, tmp_path) -> None:
    from src.ingest.core import run_ingest_mode
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    input_pdf = tmp_path / "1234_test.pdf"
    input_pdf.write_text("dummy")
    
    args = argparse.Namespace(
        input_path=str(input_pdf),
        dry_run=True,
        model=None
    )
    config = AppConfig(
        areas_root_path=str(areas_root), 
        inbox_path=str(tmp_path),
        groq_api_key="mock", 
        openai_api_key="mock"
    )
    
    with patch("src.ingest.core.process_unclassified_pdf") as mock_process:
        def mock_process_side_effect(**kwargs):
            raw_dump_path = input_pdf.parent / f"{input_pdf.stem}.raw_dump.json"
            raw_dump_path.write_text('{"groups": [{"expected_house_number": "1234", "expected_tenant_name": "Tenant", "category": "cat", "start_page": 0, "end_page": 0}]}')
        mock_process.side_effect = mock_process_side_effect
        
        with patch("pypdf.PdfReader") as mock_pdf_reader:
            mock_pdf_reader.return_value.pages = [1]
            run_ingest_mode(args, config, None)
            
    mock_print_summary.assert_called_once()


@patch("src.pipeline.visualizer.Visualizer.print_summary")
def test_reconcile_dry_run_calls_visualizer(mock_print_summary, tmp_path) -> None:
    from src.reconcile.core import run_reconcile_mode
    target_dir = tmp_path / "1234 - Tenant"
    target_dir.mkdir()
    source_dir = target_dir / ".source_files"
    source_dir.mkdir()
    
    yaml_path = source_dir / "1234_1_tenants.yaml"
    yaml_path.write_text("- name: Tenant\n  start_date: '2020-01-01'\n  end_date: present\n")
    
    state_file = source_dir / "1234_state.json"
    state_file.write_text('{"cleaned_pages": [], "grouped_documents": [], "manifest": {"per_page": []}}')
    
    args = argparse.Namespace(
        target_dir=target_dir,
        dry_run=True
    )
    
    run_reconcile_mode(args)
    
    mock_print_summary.assert_called_once()

