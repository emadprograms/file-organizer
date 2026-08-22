import pytest
from pathlib import Path
import json
import yaml
import os
import shutil
from unittest.mock import MagicMock, patch

from src.main import get_parser
from src.ingest.core import run_ingest_mode
from src.reconcile.core import run_reconcile_mode
from src.core.config import AppConfig
from src.core.schemas import DocumentGroup
from src.core.models import PageData

class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@patch("src.pipeline.pipeline.Pipeline._clean_documents")
@patch("src.categorization.fine_categorization.process_fine_categorization")
@patch("src.pipeline.pipeline.Pipeline._group_documents")
@patch("src.pipeline.pipeline.Pipeline._route_documents")
def test_ingest_and_reconcile_workflow(mock_route, mock_group, mock_fine, mock_clean, tmp_path):
    # Setup mock house and config
    house_id = "777"
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    target_dir = areas_root / f"{house_id} - Test House"
    target_dir.mkdir(parents=True, exist_ok=True)
    source_dir = target_dir / ".source_files"
    
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump({"areas_root_path": str(areas_root), "inbox_path": str(tmp_path / "inbox")}, f)

    config = AppConfig.load(config_path)
    
    
    
    # Create a raw PDF in inbox
    raw_pdf_path = target_dir / "777.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(raw_pdf_path, "wb") as f:
        writer.write(f)
        
    # Flat list raw dump json
    dump_data = [
        {
            "expected_house_number": house_id,
            "expected_tenant_name": "Test Tenant",
            "category": "others",
            "date": "2021-06-01",
            "content_explanation": "Test invoice"
        }
    ]
    
    dump_path = target_dir / "777.raw_dump.json"
    with open(dump_path, "w") as f:
        json.dump(dump_data, f)

    # Setup mocks
    mock_clean.return_value = (
        [PageData(
            category="others", date="2021-06-01", original_index=0, status="success",
            expected_house_number=house_id, expected_tenant_name="Test Tenant",
            content_explanation="Test invoice"
        )],
        [{"name": "Test Tenant", "start_date": "2021-01-01", "end_date": "2025-01-01"}]
    )
    mock_fine.return_value = mock_clean.return_value[0]
    mock_group.return_value = [DocumentGroup(
        start_page=0, end_page=0, primary_tenant="Test Tenant",
        category="others", dates=["2021-06-01"], reason="mock",
        brief_arabic_title="Mock", folder_path="Others", is_direct_routed=True
    )]
    mock_route.return_value = mock_group.return_value

    args = DummyArgs(command="ingest", input_path=target_dir, dry_run=False, verbose=False)
    mock_llm = MagicMock()

    # Run ingest
    result = run_ingest_mode(args, config, mock_llm)
    assert result == 0
    
    # Check that PDF was moved to target house directory and manifest created
    target_dir = areas_root / "777 - Test Tenant"
    ingested_pdf = target_dir / "777.pdf"
    assert ingested_pdf.exists()
    sidecar_json = target_dir / "777_ingest_manifest.json"
    assert sidecar_json.exists()
    
    # Check that state.json was created
    source_dir = target_dir / ".source_files"
    state_file = source_dir / "777_state.json"
    assert state_file.exists(), "ingest should generate state.json"
    
    with open(state_file, "r", encoding="utf-8") as f:
        state_data = json.load(f)
        assert "cleaned_pages" in state_data
        assert "grouped_documents" in state_data
        assert "routed_documents" in state_data
        assert "per_page" in state_data["routed_documents"]
        assert len(state_data["routed_documents"]["per_page"]) == 1
        
    # Now run reconcile
    rec_args = DummyArgs(command="reconcile", target_dir=target_dir, dry_run=False, verbose=False, tenants=False)
    result = run_reconcile_mode(rec_args)
    assert result == 0
    
    # Reconcile should have generated the output files and updated the state with vault_ids
    new_state_file = list(areas_root.glob("777*/.source_files/777_state.json"))[0]
    with open(new_state_file, "r", encoding="utf-8") as f:
        state_data = json.load(f)
        
        assert "per_page" in state_data["routed_documents"]
        assert len(state_data["routed_documents"]["per_page"]) == 1
        
        page = state_data["routed_documents"]["per_page"][0]
        assert "output_file" in page
        assert "vault_id" in page

