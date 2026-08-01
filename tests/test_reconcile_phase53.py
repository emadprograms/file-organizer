import pytest
from pathlib import Path
import json
import yaml
import shutil
from unittest.mock import patch

from src.reconcile.core import run_reconcile_mode

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"

def test_nested_folder_trap_phase53(tmp_path):
    house_id = "515"
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [
        {"name": "Ahmed", "start_date": "2021-01-01", "end_date": "present"}
    ]
    with open(source_dir / f"{house_id}_tenants.yaml", "w") as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [{
            "page_index": 0, 
            "canonical_tenant": "Ahmed", 
            "resolved_date": "2021-05-11", 
            "topics": ["01_Cat"], 
            "is_junk": False,
            "category": "personal",
            "content_explanation": "mock explanation",
            "original_index": 0
        }],
        "grouped_documents": [{
            "start_page": 0, 
            "end_page": 0, 
            "primary_tenant": "Ahmed", 
            "primary_topic": "01_Cat", 
            "metadata": {"date": "2021-05-11"}, 
            "issues": [], 
            "language": "ar",
            "category": "personal",
            "dates": ["2021-05-11"],
            "vault_id": "test_vault_1"
        }],
        "manifest": {
            "per_page": [
                {
                    "page_index": 0,
                    "tenant": "Ahmed",
                    "target_folder": "Ahmed/01_Cat/Sub/Deep",
                    "output_file": f"{house_id} - Ahmed/Ahmed/01_Cat/Sub/Deep/doc.lnk",
                    "vault_id": "test_vault_1"
                }
            ]
        }
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)
    vault_pdf = vault_dir / "doc_test_vault_1.pdf"
    vault_pdf.touch()
    
    # Create the physical shortcut to prevent it from being seen as user-deleted
    old_lnk_path = target_dir / "Ahmed/01_Cat/Sub/Deep/doc.lnk"
    old_lnk_path.parent.mkdir(parents=True, exist_ok=True)
    
    from src.utils.fs import create_shortcut
    create_shortcut(str(vault_pdf.resolve()), str(old_lnk_path.resolve()))
    
    args = DummyArgs(target_dir=target_dir)
    
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Ahmed": "Ahmed Folder"}, "Ahmed Folder")
        
        result = run_reconcile_mode(args)
    
    assert result == 0
    
    new_house_dir = tmp_path / f"{house_id} - Ahmed Folder"
    deep_lnk = new_house_dir / "Ahmed Folder/01_Cat/Sub/Deep/doc.lnk"
    assert deep_lnk.exists(), "The nested shortcut must be regenerated."
    
    with open(new_house_dir / ".source_files" / f"{house_id}_state.json") as f:
        new_state = json.load(f)
        
    assert new_state["manifest"]["per_page"][0]["target_folder"] == "Ahmed Folder/01_Cat/Sub/Deep", "State should preserve nested hierarchy."
