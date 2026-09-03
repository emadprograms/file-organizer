import pytest
import shutil
from pathlib import Path
from src.reconcile.core import run_reconcile_mode
from src.core.state import State
import yaml
import json
from src.utils.fs import create_shortcut

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = target_dir
        self.dry_run = dry_run

def test_tenant_root_folder_renaming(tmp_path):
    house_id = "54"
    target_dir = tmp_path / f"{house_id} - Current Tenant"
    target_dir.mkdir(parents=True)
    
    source_dir = target_dir / ".source_files"
    source_dir.mkdir()
    
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    
    # Create tenants.yaml
    yaml_data = [
        {"name": "Current Tenant", "start_date": "2020", "end_date": "present"},
        {"name": "Old Tenant", "start_date": "2018", "end_date": "2020"}
    ]
    with open(source_dir / "54_tenants.yaml", "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f)
        
    # Create state
    state = State(house_id, source_dir)
    state.data = {
        "cleaned_pages": [
            {
                "original_index": 0,
                "category": "contract",
                "content_explanation": "Test explanation",
                "canonical_tenant": "Current Tenant",
                "date": "2021-01-01",
                "resolved_date": "2021-01-01"
            }
        ],
        "grouped_documents": [
            {
                "start_page": 0,
                "end_page": 0,
                "primary_tenant": "Current Tenant",
                "category": "contract",
                "dates": ["2021-01-01"],
                "vault_id": "v1"
            }
        ],
        "manifest": {
            "per_page": [
                {
                    "page_index": 0,
                    "vault_id": "v1",
                    "output_file": f"{target_dir.name}/Current Tenant \u200e(2020 - الآن)\u200e/01_contract/doc.lnk",
                    "target_folder": "Current Tenant \u200e(2020 - الآن)\u200e/01_contract"
                }
            ]
        }
    }
    state.save()
    
    # Create vault pdf
    with open(vault_dir / "doc_v1.pdf", "wb") as f:
        f.write(b"%PDF-1.4\n")
        
    # User renamed the canonical folder to "My Custom Folder"
    custom_folder = target_dir / "My Custom Folder"
    custom_folder.mkdir()
    
    topic_folder = custom_folder / "01_contract"
    topic_folder.mkdir()
    
    lnk_path = topic_folder / "doc.lnk"
    create_shortcut(str(vault_dir / "doc_v1.pdf"), str(lnk_path))
    
    # Run reconciliation
    args = DummyArgs(target_dir)
    assert run_reconcile_mode(args) == 0
    
    # Check that "My Custom Folder" was deleted
    assert not custom_folder.exists()
    
    # Check that it was moved to canonical folder
    canonical_folder = target_dir / "Current Tenant \u200e(2020 - الآن)\u200e"
    assert canonical_folder.exists()
    assert (canonical_folder / "01_contract" / "doc.lnk").exists()
    
    # Check state
    state2 = State(house_id, source_dir)
    p = state2.data["manifest"]["per_page"][0]
    assert "Current Tenant" in p["target_folder"]
    assert not p.get("user_locked", False)
