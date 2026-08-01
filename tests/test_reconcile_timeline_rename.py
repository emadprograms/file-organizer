import pytest
from pathlib import Path
import json
import yaml
from unittest.mock import patch

from src.reconcile.core import run_reconcile_mode

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"

def test_run_reconcile_mode_timeline_view_after_rename(tmp_path):
    """
    Test that the [Timeline View] shortcuts are generated with the correct absolute paths
    AFTER the target directory is renamed.
    """
    house_id = "999"
    target_dir = tmp_path / f"{house_id} - Old House"
    source_dir = target_dir / ".source_files"
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)
    
    # Create dummy vault pdf
    (vault_dir / "doc_vault123.pdf").touch()
    
    yaml_data = [
        {"name": "New Tenant", "start_date": "2021-01-01", "end_date": "present"}
    ]
    with open(source_dir / f"{house_id}_tenants.yaml", "w") as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [{
            "page_index": 0, 
            "canonical_tenant": "New Tenant", 
            "resolved_date": "2021-05-11", 
            "topics": ["02"], 
            "is_junk": False,
            "category": "personal",
            "content_explanation": "mock explanation",
            "original_index": 0,
            "vault_id": "vault123"
        }],
        "grouped_documents": [{
            "start_page": 0, 
            "end_page": 0, 
            "primary_tenant": "New Tenant", 
            "primary_topic": "02", 
            "metadata": {"date": "2021-05-11"}, 
            "issues": [], 
            "language": "ar",
            "category": "personal",
            "dates": ["2021-05-11"],
            "vault_id": "vault123"
        }],
        "manifest": {
            "per_page": [
                {
                    "page_index": 0,
                    "tenant": "New Tenant",
                    "target_folder": "New Tenant/02",
                    "output_file": f"{house_id} - Old House/New Tenant/02/2021-05-11.lnk",
                    "vault_id": "vault123",
                    "dates": ["2021-05-11"],
                    "brief_arabic_title": "test_doc"
                }
            ]
        }
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    old_output_path = tmp_path / f"{house_id} - Old House/New Tenant/02/2021-05-11.lnk"
    old_output_path.parent.mkdir(parents=True, exist_ok=True)
    old_output_path.touch()
        
    args = DummyArgs(target_dir=target_dir)
    
    with patch("src.reconcile.core.FileOrganizer") as mock_org, \
         patch("src.utils.fs.batch_create_shortcuts") as mock_batch_shortcuts, \
         patch("src.utils.fs.batch_read_shortcut_targets") as mock_batch_read_shortcut_targets:
             
        mock_batch_read_shortcut_targets.return_value = {
            str(old_output_path.resolve()): str((vault_dir / "doc_vault123.pdf").resolve())
        }
             
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"New Tenant": "New Tenant (2021 - now)"}, "New Tenant (2021 - now)")
        
        result = run_reconcile_mode(args)
    
    assert result == 0, "Reconcile mode should succeed"
    
    new_house_dir = tmp_path / f"{house_id} - New Tenant (2021 - now)"
    
    # Assert timeline view shortcut creation was called with new_house_dir
    timeline_shortcut_creation = None
    for call in mock_batch_shortcuts.mock_calls:
        shortcuts_list = call.args[0]
        for shortcut in shortcuts_list:
            if "Timeline View" in shortcut["link"]:
                timeline_shortcut_creation = shortcut
                break
        if timeline_shortcut_creation:
            break
            
    assert timeline_shortcut_creation is not None, "Timeline view shortcut should have been created"
    
    # Check that target path correctly uses the new house dir, NOT the old target_dir
    target_path = timeline_shortcut_creation["target"]
    assert str(new_house_dir.resolve()) in target_path
    assert str(target_dir.resolve()) not in target_path
