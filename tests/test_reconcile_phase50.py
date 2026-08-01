import pytest
import os
import json
from pathlib import Path
from src.utils.fs import create_shortcut
from src.reconcile.core import run_reconcile_mode
import uuid
import yaml

class MockArgs:
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.dry_run = False

def setup_house_for_phase50(tmp_path):
    house_id = "550"
    tenant_name = "Phase50Tenant"
    target_dir = tmp_path / f"{house_id} - {tenant_name}"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    source_dir = target_dir / ".source_files"
    source_dir.mkdir()
    
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    
    tenant_dir = target_dir / tenant_name
    tenant_dir.mkdir()
    category_dir = tenant_dir / "عقود"
    category_dir.mkdir()
    
    # Tenants YAML
    yaml_path = source_dir / f"{house_id}_tenants.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump([{"name": tenant_name, "start_date": "2020-01-01", "end_date": "present"}], f, allow_unicode=True)
        
    vault_id = uuid.uuid4().hex
    vault_pdf = vault_dir / f"doc_{vault_id}.pdf"
    vault_pdf.write_text("dummy")
    
    # Create the primary shortcut (valid)
    primary_lnk = category_dir / "2020-01-01 - valid.lnk"
    create_shortcut(str(vault_pdf), str(primary_lnk))
    
    # State setup
    state_file = source_dir / f"{house_id}_state.json"
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [
            {
                "category": "عقود",
                "content_explanation": "Test",
                "expected_tenant_name": tenant_name,
                "original_index": 0
            }
        ],
        "grouped_documents": [
            {
                "start_page": 0,
                "end_page": 0,
                "primary_tenant": tenant_name,
                "category": "عقود",
                "dates": ["2020-01-01"],
                "vault_id": vault_id,
                "shortcuts": [f"{tenant_name}/عقود/2020-01-01 - valid.lnk"]
            }
        ],
        "manifest": {
            "per_page": [
                {
                    "page_index": 0,
                    "vault_id": vault_id,
                    "output_file": f"{target_dir.name}/{tenant_name}/عقود/2020-01-01 - valid.lnk",
                    "target_folder": f"{tenant_name}/عقود"
                }
            ]
        }
    }
    
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f, ensure_ascii=False)
        
    return target_dir, vault_id

def test_phase50_external_shortcut_ignored(tmp_path):
    target_dir, valid_vault_id = setup_house_for_phase50(tmp_path)
    
    # Create an external directory and dummy vault file
    external_dir = tmp_path / "other_house"
    external_dir.mkdir()
    external_vault = external_dir / "doc_999999.pdf"
    external_vault.write_text("external data")
    
    # Place a shortcut inside our house pointing to the external vault
    category_dir = target_dir / "Phase50Tenant" / "عقود"
    external_lnk = category_dir / "2020-01-02 - external.lnk"
    create_shortcut(str(external_vault), str(external_lnk))
    
    args = MockArgs(target_dir)
    res = run_reconcile_mode(args)
    assert res == 0
    
    state_file = target_dir / ".source_files" / "550_state.json"
    with open(state_file, "r", encoding="utf-8") as f:
        state_data = json.load(f)
        
    # The external shortcut should be ignored, so no ghost adoption, no new pages
    assert len(state_data["cleaned_pages"]) == 1
    assert len(state_data["grouped_documents"]) == 1
    
    group = state_data["grouped_documents"][0]
    # No extra shortcut in the group since the external one is skipped
    assert len(group.get("shortcuts", [])) == 1
