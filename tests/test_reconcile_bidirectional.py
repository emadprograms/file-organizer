import os
import json
import pytest
from pathlib import Path
from types import SimpleNamespace
import yaml

from src.reconcile.core import run_reconcile_mode
from src.utils.fs import create_shortcut

def test_bidirectional_reconciliation_user_locking(tmp_path):
    target_dir = tmp_path / "502 - Unassigned"
    target_dir.mkdir()
    
    source_dir = target_dir / ".source_files"
    source_dir.mkdir()
    
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    
    # Create mock vault PDF
    vault_pdf = vault_dir / "doc_mock_vault.pdf"
    vault_pdf.touch()
    
    # Create tenants yaml
    yaml_path = source_dir / "502_tenants.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump([
            {"name": "NewTenant", "start_date": "2023-01-01", "end_date": "present"}
        ], f)
        
    # Create state files
    state_data = {
        "house_id": "502",
        "cleaned_pages": [
            {
                "page_index": 0,
                "text": "mock",
                "canonical_tenant": "Unassigned",
                "user_locked": False,
                "dates": ["2022-01-01"],
                "category": "Unknown",
                "content_explanation": "mock explanation",
                "original_index": 0
            }
        ],
        "grouped_documents": [
            {
                "start_page": 0,
                "end_page": 0,
                "primary_tenant": "Unassigned",
                "user_locked": False,
                "category": "Unknown",
                "dates": ["2022-01-01"],
                "vault_id": "mock_vault"
            }
        ],
        "manifest": {
            "per_page": [
                {
                    "page_index": 0,
                    "target_folder": "Unassigned",
                    "output_file": "502 - Unassigned/Unassigned/mock.lnk",
                    "vault_id": "mock_vault"
                }
            ]
        }
    }
    with open(source_dir / "502_state.json", 'w') as f:
        json.dump(state_data, f)
        
    # We pretend the user moved the shortcut from Unassigned to MovedByUser
    moved_dir = target_dir / "MovedByUser"
    moved_dir.mkdir()
    shortcut_path = moved_dir / "mock.lnk"
    create_shortcut(str(vault_pdf.resolve()), str(shortcut_path))
    
    args = SimpleNamespace(target_dir=target_dir, dry_run=False)
    
    # Run reconciliation
    res = run_reconcile_mode(args)
    assert res == 0
    
    # Verify that the directory was NOT renamed to 502 - NewTenant because user lock keeps it?
    # Wait, the latest tenant will be NewTenant according to tenants.yaml, so the house dir will be renamed
    # to 502 - NewTenant. Let's find it.
    new_house_dir = tmp_path / "502 - NewTenant"
    assert new_house_dir.exists()
    
    # Verify state was updated with user_locked
    new_source_dir = new_house_dir / ".source_files"
    with open(new_source_dir / "502_state.json", 'r') as f:
        new_data = json.load(f)
        
    p = new_data["manifest"]["per_page"][0]
    assert p["target_folder"] == "MovedByUser"
    assert p["user_locked"] is True
    
    # Also verify the cleaned/grouped logic
    cp = new_data["cleaned_pages"][0]
    assert cp["user_locked"] is True
    
    gp = new_data["grouped_documents"][0]
    assert gp["user_locked"] is True
        
    # Check that [Timeline View] was generated
    timeline_dir = new_house_dir / "[Timeline View]"
    assert timeline_dir.exists()
    shortcuts = list(timeline_dir.glob("*.lnk"))
    assert len(shortcuts) == 1
    
