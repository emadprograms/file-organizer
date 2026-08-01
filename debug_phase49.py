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

def debug_run():
    # Setup
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_path = Path(tmp_str)
        house_id = "500"
        tenant_name = "Phase49Tenant"
        target_dir = tmp_path / f"{house_id} - {tenant_name}"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        source_dir = target_dir / ".source_files"
        source_dir.mkdir()
        
        vault_dir = source_dir / "vault"
        vault_dir.mkdir()
        
        tenant_dir = target_dir / tenant_name
        tenant_dir.mkdir()
        category_dir = tenant_dir / "رسائل"
        category_dir.mkdir()
        
        # Tenants YAML
        yaml_path = source_dir / f"{house_id}_tenants.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump([{"name": tenant_name, "start_date": "2020-01-01", "end_date": "present"}], f, allow_unicode=True)
            
        vault_id = uuid.uuid4().hex
        vault_pdf = vault_dir / f"doc_{vault_id}.pdf"
        vault_pdf.write_text("dummy")
        
        primary_lnk = category_dir / "2020-01-01 - primary.lnk"
        create_shortcut(str(vault_pdf), str(primary_lnk))
        
        duplicate_lnk = category_dir / "2020-01-01 - duplicate.lnk"
        create_shortcut(str(vault_pdf), str(duplicate_lnk))
        
        state_file = source_dir / f"{house_id}_state.json"
        state_data = {
            "house_id": house_id,
            "cleaned_pages": [
                {
                    "category": "رسائل",
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
                    "category": "رسائل",
                    "dates": ["2020-01-01"],
                    "vault_id": vault_id,
                    "shortcuts": [f"{tenant_name}/رسائل/2020-01-01 - primary.lnk"]
                }
            ],
            "manifest": {
                "per_page": [
                    {
                        "page_index": 0,
                        "vault_id": vault_id,
                        "output_file": f"{target_dir.name}/{tenant_name}/رسائل/2020-01-01 - primary.lnk",
                        "target_folder": f"{tenant_name}/رسائل"
                    }
                ]
            }
        }
        
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f, ensure_ascii=False)
            
        args = MockArgs(target_dir)
        res = run_reconcile_mode(args)
        print("Reconcile returned:", res)
        
        timeline_dir = target_dir / "[Timeline View]"
        print("Timeline exists:", timeline_dir.exists())
        if timeline_dir.exists():
            print("Timeline links:", list(timeline_dir.glob("*.lnk")))
            
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)
            print("Shortcuts in group:", state_data["grouped_documents"][0].get("shortcuts"))

if __name__ == "__main__":
    debug_run()
