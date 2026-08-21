import pytest
from pathlib import Path
import json
import yaml
import shutil
from unittest.mock import patch

from src.reconcile.core import run_reconcile_mode
from src.utils.fs import create_shortcut

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"

def test_phase43_raw_pdf_ingestion(tmp_path):
    house_id = "100"
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [
        {"name": "Tenant", "start_date": "2021-01-01", "end_date": "present"}
    ]
    with open(source_dir / f"{house_id}_tenants.yaml", "w") as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [],
        "grouped_documents": [],
        "manifest": {"per_page": []}
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    # Drop a raw PDF in a subfolder inside a canonical tenant
    subfolder = target_dir / "Tenant" / "others"
    subfolder.mkdir(parents=True)
    raw_pdf = subfolder / "2023-05-15 - Raw Invoice.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(raw_pdf, "wb") as f:
        writer.write(f)
    
    args = DummyArgs(target_dir=target_dir)
    
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Tenant": "Tenant"}, "Tenant")
        result = run_reconcile_mode(args)
    
    assert result == 0
    
    # 1. Raw PDF should be gone from the subfolder
    new_house_dir = tmp_path / f"{house_id} - Tenant"
    new_subfolder = new_house_dir / "Tenant" / "others"
    assert not (new_subfolder / "2023-05-15 - Raw Invoice.pdf").exists()
    
    # 2. A shortcut should be in its place
    shortcut = new_subfolder / "2023-05-15---Raw-Invoice_page_1.lnk"
    assert shortcut.exists()
    
    # 3. State should have been updated with user_locked=True and vault_id
    with open(new_house_dir / ".source_files" / f"{house_id}_state.json") as f:
        new_state = json.load(f)
        
    assert len(new_state["cleaned_pages"]) == 1
    assert len(new_state["grouped_documents"]) == 1
    per_page = new_state["manifest"]["per_page"]
    assert len(per_page) == 1
    
    p = per_page[0]
    assert p["user_locked"] is True
    assert p["date"] == "2023-05-15"
    assert "vault_id" in p
    
    # 4. Vault PDF should exist
    vault_id = p["vault_id"]
    vault_pdf = new_house_dir / ".source_files" / "vault" / f"doc_{vault_id}.pdf"
    assert vault_pdf.exists()


def test_phase43_ghost_shortcut_adoption(tmp_path):
    house_id = "101"
    target_dir = tmp_path / f"{house_id} - Ghost House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [
        {"name": "Tenant", "start_date": "2021-01-01", "end_date": "present"}
    ]
    with open(source_dir / f"{house_id}_tenants.yaml", "w") as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [],
        "grouped_documents": [],
        "manifest": {"per_page": []}
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)
    vault_pdf = vault_dir / "doc_mockvault123.pdf"
    vault_pdf.touch()
    
    # Create ghost shortcut
    subfolder = target_dir / "GhostFolder"
    subfolder.mkdir(parents=True)
    shortcut_path = subfolder / "2022-11-20 - Ghost Doc.lnk"
    create_shortcut(str(vault_pdf.resolve()), str(shortcut_path.resolve()))
    
    args = DummyArgs(target_dir=target_dir)
    
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Tenant": "Tenant"}, "Tenant")
        result = run_reconcile_mode(args)
        
    assert result == 0
    
    new_house_dir = tmp_path / f"{house_id} - Tenant"
    with open(new_house_dir / ".source_files" / f"{house_id}_state.json") as f:
        new_state = json.load(f)
        
    assert len(new_state["cleaned_pages"]) == 1
    per_page = new_state["manifest"]["per_page"]
    assert len(per_page) == 1
    
    p = per_page[0]
    assert p["user_locked"] is False
    assert p["date"] == "2022-11-20"
    assert p["vault_id"] == "mockvault123"
