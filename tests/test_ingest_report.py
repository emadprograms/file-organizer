import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.ingest.core import run_ingest_mode
from src.core.config import AppConfig

class DummyArgs:
    def __init__(self, input_path, dry_run=False):
        self.input_path = input_path
        self.dry_run = dry_run

from src.core.models import PageData
from src.core.schemas import DocumentGroup

@patch("src.pipeline.pipeline.Pipeline._clean_documents")
@patch("src.categorization.fine_categorization.process_fine_categorization")
@patch("src.pipeline.pipeline.Pipeline._group_documents")
@patch("src.pipeline.pipeline.Pipeline._route_documents")
def test_ingest_report_generated(mock_route, mock_group, mock_fine, mock_clean, tmp_path):
    mock_clean.return_value = (
        [
            PageData(category="others", date="2024-01-01", original_index=0, expected_tenant_name="John Doe", canonical_tenant="John Doe"),
            PageData(category="others", date="2024-01-01", original_index=1, expected_tenant_name="John Doe", canonical_tenant="John Doe")
        ],
        [{"name": "John Doe", "start_date": "2021-01-01", "end_date": "present"}]
    )
    mock_fine.return_value = mock_clean.return_value[0]
    mock_group.return_value = [DocumentGroup(
        start_page=0, end_page=1, primary_tenant="John Doe",
        category="others", dates=["2024-01-01"], reason="mock"
    )]
    mock_route.return_value = [DocumentGroup(
        start_page=0, end_page=1, primary_tenant="John Doe",
        category="others", dates=["2024-01-01"], reason="mock", vault_id="new_vault"
    )]
    # Setup directories
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    pdf_file = input_dir / "711.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100)
    with open(pdf_file, "wb") as f:
        writer.write(f)

    areas_root = tmp_path / "areas"
    areas_root.mkdir()

    config = AppConfig(areas_root_path=str(areas_root), provider="test", inbox_path=str(input_dir))

    dump_data = [
        {
            "expected_house_number": "711",
            "expected_tenant_name": "John Doe",
            "category": "others",
            "date": "2024-01-01"
        },
        {
            "expected_house_number": "711",
            "expected_tenant_name": "John Doe",
            "category": "others",
            "date": "2024-01-01"
        }
    ]
    dump_path = input_dir / "711.raw_dump.json"
    with open(dump_path, "w") as f:
        json.dump(dump_data, f)

    args = DummyArgs(input_path=str(input_dir), dry_run=False)
    llm_client = MagicMock()

    ret = run_ingest_mode(args, config, llm_client)
    assert ret == 0

    target_house_dir = input_dir / "711 - John Doe"
    source_files = target_house_dir / ".source_files"
    assert source_files.exists()
        
    report_path = source_files / "ingest_report.json"
    assert report_path.exists(), "ingest_report.json was not generated"
        
    with open(report_path, "r") as f:
        report_data = json.load(f)
            
        assert report_data["pdfs_processed"] == 1
        assert report_data["errors"] == 0
        assert report_data["pages_ingested"] == 2
