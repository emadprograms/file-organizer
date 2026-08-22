import pytest
import shutil
import json
from pathlib import Path
from src.reconcile.core import run_reconcile_mode
from src.core.state import State
import yaml
from src.utils.fs import create_shortcut

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = target_dir
        self.dry_run = dry_run

def test_reconcile_auto_repair_hijacked_shortcut(tmp_path):
    house_id = "55"
    target_dir = tmp_path / f"{house_id} - Test House"
    target_dir.mkdir(parents=True)
    
    source_dir = target_dir / ".source_files"
    source_dir.mkdir()
    
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    
    yaml_data = [
        {"name": "Test Tenant", "start_date": "2020", "end_date": "present"}
    ]
    with open(source_dir / "55_tenants.yaml", "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f)
        
    state = State(house_id, source_dir)
    state.data = {
        "cleaned_pages": [
            {
                "original_index": 0,
                "category": "contract",
                "content_explanation": "Test",
                "canonical_tenant": "Test Tenant",
                "date": "2021-01-01",
                "resolved_date": "2021-01-01"
            }
        ],
        "grouped_documents": [
            {
                "start_page": 0,
                "end_page": 0,
                "primary_tenant": "Test Tenant",
                "category": "contract",
                "dates": ["2021-01-01"],
                "vault_id": "v1"
            }
        ],
        "routed_documents": {
            "per_page": [
                {
                    "page_index": 0,
                    "vault_id": "v1",
                    "output_file": f"{target_dir.name}/Test Tenant \u200e(2020 - الآن)\u200e/01_contract/doc.lnk",
                    "target_folder": "Test Tenant \u200e(2020 - الآن)\u200e/01_contract"
                }
            ]
        }
    }
    state.save()
    
    from pypdf import PdfWriter
    def create_mock_pdf(path):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        with open(path, "wb") as f:
            writer.write(f)

    # Create the correct vault PDF and a wrong one
    create_mock_pdf(vault_dir / "doc_v1.pdf")
    create_mock_pdf(vault_dir / "doc_wrong.pdf")
        
    topic_folder = target_dir / "Test Tenant \u200e(2020 - الآن)\u200e" / "01_contract"
    topic_folder.mkdir(parents=True)
    
    lnk_path = topic_folder / "doc.lnk"
    # Hijack the shortcut to point to doc_wrong.pdf
    create_shortcut(str(vault_dir / "doc_wrong.pdf"), str(lnk_path))
    
    args = DummyArgs(target_dir)
    assert run_reconcile_mode(args) == 0
    
    # The house directory gets renamed to "55 - Test Tenant" during reconciliation
    new_target_dir = tmp_path / f"{house_id} - Test Tenant"
    new_vault_dir = new_target_dir / ".source_files" / "vault"
    
    # Check that vault PDF v1 was NOT deleted
    assert (new_vault_dir / "doc_v1.pdf").exists()
    
    # Check that the shortcut was rewritten to point to v1
    from src.utils.fs import read_shortcut_target
    new_lnk_path = new_target_dir / "Test Tenant \u200e(2020 - الآن)\u200e" / "01_contract" / "doc.lnk"
    target = read_shortcut_target(str(new_lnk_path))
    assert "doc_v1.pdf" in target
    
    # Check report
    report_file = new_target_dir / ".source_files" / "reconcile_report.json"
    with open(report_file, "r", encoding="utf-8") as f:
        report = json.load(f)
    assert report.get("shortcuts_repaired") == 1
