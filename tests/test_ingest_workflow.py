import pytest
from pathlib import Path
import json
import yaml
import os
import shutil

from src.main import get_parser
from src.ingest.core import run_ingest_mode
from src.reconcile.core import run_reconcile_mode
from src.core.config import AppConfig

class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_ingest_workflow(tmp_path):
    # Setup mock house and config
    house_id = "777"
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    target_dir = areas_root / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [
        {"name": "Test Tenant", "start_date": "2021-01-01", "end_date": "2025-01-01"}
    ]
    with open(source_dir / f"{house_id}_tenants.yaml", "w", encoding='utf-8') as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [],
        "grouped_documents": [],
        "manifest": {
            "per_page": []
        }
    }
    with open(source_dir / f"{house_id}_state.json", "w", encoding='utf-8') as f:
        json.dump(state_data, f)

    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump({"areas_root_path": str(areas_root), "inbox_path": str(tmp_path / "inbox")}, f)

    config = AppConfig.load(config_path)
    
    inbox_dir = tmp_path / "inbox"
    
    # Create a raw PDF in inbox
    raw_pdf_path = inbox_dir / "777.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(raw_pdf_path, "wb") as f:
        writer.write(f)
        
    dump_data = {
        "groups": [
            {
                "expected_house_number": house_id,
                "expected_tenant_name": "Test Tenant",
                "category": "others",
                "start_page": 0,
                "end_page": 0,
                "date": "2021-06-01",
                "content_explanation": "Test invoice"
            }
        ]
    }
    dump_path = inbox_dir / "777.raw_dump.json"
    with open(dump_path, "w") as f:
        json.dump(dump_data, f)

    args = DummyArgs(command="ingest", input_path=inbox_dir, dry_run=False, verbose=False)

    # Run ingest
    result = run_ingest_mode(args, config, None)
    assert result == 0
    
    # Check that PDF was moved to target house directory and sidecar created
    ingested_pdf = target_dir / "777.pdf"
    assert ingested_pdf.exists()
    sidecar_json = target_dir / "777_ingest_manifest.json"
    assert sidecar_json.exists()
    
    with open(sidecar_json, "r", encoding="utf-8") as f:
        sidecar_data = json.load(f)
        assert len(sidecar_data["groups"]) == 1
        assert sidecar_data["groups"][0]["expected_tenant_name"] == "Test Tenant"
