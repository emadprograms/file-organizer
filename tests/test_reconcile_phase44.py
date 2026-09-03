import pytest
from pypdf import PdfWriter
def make_valid_pdf(path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(path, "wb") as f:
        writer.write(f)

from pathlib import Path
import json
import yaml
from unittest.mock import patch

from src.reconcile.core import run_reconcile_mode
from src.utils.fs import create_shortcut

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"

def test_phase44_user_deletion(tmp_path):
    house_id = "102"
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
        "cleaned_pages": [{
            "category": "misc",
            "content_explanation": "test",
            "original_index": 0,
            "user_locked": False,
            "canonical_tenant": "Tenant"
        }],
        "grouped_documents": [{
            "start_page": 0,
            "end_page": 0,
            "primary_tenant": "Tenant",
            "category": "misc",
            "dates": []
        }],
        "manifest": {"per_page": [{
            "page_index": 0,
            "vault_id": "delete_me_123",
            "target_folder": "Tenant/Misc",
            "output_file": f"{house_id} - Tenant/Tenant/Misc/2021.lnk",
            "tenant": "Tenant"
        }]}
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    vault_pdf = vault_dir / "doc_delete_me_123.pdf"
    make_valid_pdf(vault_pdf)
    
    # We DO NOT create the shortcut, simulating user deletion
    args = DummyArgs(target_dir=target_dir)
    
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Tenant": "Tenant"}, "Tenant")
        result = run_reconcile_mode(args)
        
    assert result == 0
    
    new_house_dir = tmp_path / f"{house_id} - Tenant"
    with open(new_house_dir / ".source_files" / f"{house_id}_state.json") as f:
        new_state = json.load(f)
        
    # Should be removed from state
    assert len(new_state["cleaned_pages"]) == 0
    assert len(new_state["grouped_documents"]) == 0
    assert len(new_state["manifest"]["per_page"]) == 0
    
    # Vault PDF should be trashed
    assert not (new_house_dir / ".source_files" / "vault" / "doc_delete_me_123.pdf").exists()
    assert (new_house_dir / ".source_files" / ".trash" / "doc_delete_me_123.pdf").exists()


def test_phase44_orphan_cleanup(tmp_path):
    house_id = "103"
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
        
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    vault_pdf = vault_dir / "doc_orphan_456.pdf"
    make_valid_pdf(vault_pdf)
    
    args = DummyArgs(target_dir=target_dir)
    
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Tenant": "Tenant"}, "Tenant")
        result = run_reconcile_mode(args)
        
    assert result == 0
    
    new_house_dir = tmp_path / f"{house_id} - Tenant"
    
    # Vault PDF should be trashed
    assert not (new_house_dir / ".source_files" / "vault" / "doc_orphan_456.pdf").exists()
    assert (new_house_dir / ".source_files" / ".trash" / "doc_orphan_456.pdf").exists()
