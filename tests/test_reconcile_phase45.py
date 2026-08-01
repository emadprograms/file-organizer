import pytest
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

def test_phase45_renamed_shortcut(tmp_path):
    house_id = "104"
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [{"name": "Tenant", "start_date": "2021-01-01", "end_date": "present"}]
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
            "dates": [],
            "vault_id": "rename_me"
        }],
        "manifest": {"per_page": [{
            "page_index": 0,
            "vault_id": "rename_me",
            "target_folder": "Tenant",
            "output_file": f"{house_id} - Test House/Tenant/OldName.lnk",
            "tenant": "Tenant"
        }]}
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    vault_pdf = vault_dir / "doc_rename_me.pdf"
    vault_pdf.touch()
    
    # Create the renamed shortcut
    tenant_dir = target_dir / "Tenant"
    tenant_dir.mkdir(parents=True)
    new_lnk = tenant_dir / "NewName.lnk"
    create_shortcut(str(vault_pdf.resolve()), str(new_lnk.resolve()))
    
    args = DummyArgs(target_dir=target_dir)
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Tenant": "Tenant"}, "Tenant")
        result = run_reconcile_mode(args)
        
    assert result == 0
    new_house_dir = tmp_path / f"{house_id} - Tenant"
    with open(new_house_dir / ".source_files" / f"{house_id}_state.json") as f:
        new_state = json.load(f)
        
    p = new_state["manifest"]["per_page"][0]
    assert p["user_locked"] is True
    assert p["brief_arabic_title"] == "NewName"
    assert "NewName.lnk" in p["output_file"]

def test_phase45_duplicate_shortcut(tmp_path):
    house_id = "105"
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [{"name": "Tenant", "start_date": "2021-01-01", "end_date": "present"}]
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
            "dates": [],
            "vault_id": "duplicate_me"
        }],
        "manifest": {"per_page": [{
            "page_index": 0,
            "vault_id": "duplicate_me",
            "target_folder": "Tenant",
            "output_file": f"{house_id} - Test House/Tenant/Original.lnk",
            "tenant": "Tenant"
        }]}
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    vault_pdf = vault_dir / "doc_duplicate_me.pdf"
    vault_pdf.touch()
    
    tenant_dir = target_dir / "Tenant"
    tenant_dir.mkdir(parents=True)
    
    # The original shortcut
    orig_lnk = tenant_dir / "Original.lnk"
    create_shortcut(str(vault_pdf.resolve()), str(orig_lnk.resolve()))
    
    # A second shortcut (copy/paste by user)
    dup_lnk = tenant_dir / "Original - Copy.lnk"
    create_shortcut(str(vault_pdf.resolve()), str(dup_lnk.resolve()))
    
    args = DummyArgs(target_dir=target_dir)
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Tenant": "Tenant"}, "Tenant")
        result = run_reconcile_mode(args)
        
    assert result == 0
    new_house_dir = tmp_path / f"{house_id} - Tenant"
    with open(new_house_dir / ".source_files" / f"{house_id}_state.json") as f:
        new_state = json.load(f)
        
    # Should now have 1 page still, but grouped_documents has 2 shortcuts
    assert len(new_state["cleaned_pages"]) == 1
    assert len(new_state["manifest"]["per_page"]) == 1
    assert len(new_state["grouped_documents"][0]["shortcuts"]) == 2
    
    p1 = new_state["manifest"]["per_page"][0]
    
    assert p1["vault_id"] == "duplicate_me"
    
    assert "Original.lnk" in p1["output_file"]
    
    # Timeline should have 1 file
    timeline_dir = new_house_dir / "[Timeline View]"
    shortcuts = list(timeline_dir.glob("*.lnk"))
    assert len(shortcuts) == 1
