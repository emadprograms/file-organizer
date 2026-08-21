import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import uuid

from src.reconcile.core import run_reconcile_mode
from src.pdf import extract_pdf_segment, compress_pdf
import os

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"

@patch("src.pdf.extract_pdf_segment", autospec=True)
@patch("src.pdf.compress_pdf", autospec=True)
def test_group_manifest_ingestion(mock_compress, mock_extract, tmp_path):
    # Setup house structure
    house_id = "777"
    target_dir = tmp_path / f"{house_id} - Feature House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    # tenants yaml
    with open(source_dir / f"{house_id}_tenants.yaml", "w", encoding="utf-8") as f:
        f.write("- name: Test Tenant\n  start_date: '2020-01-01'\n  end_date: present\n")
        
    # state json
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [],
        "grouped_documents": [],
        "routed_documents": {"per_page": []},
        "manifest": {"per_page": []}
    }
    with open(source_dir / f"{house_id}_state.json", "w", encoding="utf-8") as f:
        json.dump(state_data, f)
        
    # Raw monolithic PDF
    raw_pdf_path = target_dir / "2020-01-01 - Monolithic PDF.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=100, height=100)
    with open(raw_pdf_path, "wb") as f:
        writer.write(f)
        
    # Group manifest
    manifest_data = {
        "groups": [
            {
                "start_page": 0,
                "end_page": 2,
                "expected_tenant_name": "Test Tenant",
                "category": "Contract",
                "content_explanation": "Segment 1"
            },
            {
                "start_page": 3,
                "end_page": 4,
                "expected_tenant_name": "Test Tenant",
                "category": "Bill",
                "content_explanation": "Segment 2"
            }
        ]
    }
    manifest_path = target_dir / "2020-01-01 - Monolithic PDF_ingest_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    args = DummyArgs(target_dir=target_dir)
    result = run_reconcile_mode(args)
    assert result == 0
    
    # Assert extraction and compression called
    assert mock_extract.call_count == 2
    assert mock_compress.call_count == 2
    
    # Cleanup should delete raw monolithic pdf or keep it? 
    # Usually we delete the raw pdf after group ingestion, or maybe not. We'll leave it as per implementation.
