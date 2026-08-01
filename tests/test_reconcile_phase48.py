import pytest
import os
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.reconcile.core import run_reconcile_mode
from src.utils.fs import create_shortcut

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"

def test_reconcile_many_to_one_grouped_document_preservation(tmp_path):
    """
    Test Phase 48 Many-to-One preservation.
    Verifies that a grouped document (e.g. 3 JSON pages mapping to 1 physical shortcut)
    is correctly matched without deleting the 'unmatched' extra JSON pages as orphans.
    """
    valid_house_dir = tmp_path / "510 - Test House"
    source_dir = valid_house_dir / ".source_files"
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)
    
    # Reconciler requires a dummy tenants yaml file to proceed
    tenants_yaml = source_dir / "_tenants.yaml"
    with open(tenants_yaml, 'w') as f:
        f.write("- name: mock\n  start_date: '2020-01-01'\n  end_date: 'present'\n")
    
    # Create the single physical vault PDF
    vault_pdf = vault_dir / "doc_test_vault_id.pdf"
    vault_pdf.touch()
    
    # Create the single physical shortcut on disk
    target_folder = valid_house_dir / "Main Category"
    target_folder.mkdir()
    shortcut_path = target_folder / "Grouped Document.lnk"
    
    # Just touch the file so os.walk finds it. We mock the target resolution anyway.
    shortcut_path.touch()
    
    # Create mock state with 3 pages pointing to the exact same vault_id and output_file
    state_file = source_dir / "510_state.json"
    mock_state = {
        "version": "5.0",
        "house_id": "510",
        "cleaned_pages": [
            {"page_index": 0, "category": "Main Category", "vault_id": "test_vault_id", "content_explanation": "mock", "original_index": 0, "date": "2026-08-01"},
            {"page_index": 1, "category": "Main Category", "vault_id": "test_vault_id", "content_explanation": "mock", "original_index": 1, "date": "2026-08-01"},
            {"page_index": 2, "category": "Main Category", "vault_id": "test_vault_id", "content_explanation": "mock", "original_index": 2, "date": "2026-08-01"}
        ],
        "grouped_documents": [
            {
                "start_page": 0,
                "end_page": 2,
                "vault_id": "test_vault_id",
                "category": "Main Category",
                "primary_tenant": "mock",
                "dates": ["2026-08-01"]
            }
        ],
        "manifest": {
            "per_page": [
                {
                    "page_index": 0,
                    "vault_id": "test_vault_id",
                    "output_file": "510 - Test House/Main Category/Grouped Document.lnk",
                    "target_folder": "510 - Test House/Main Category"
                },
                {
                    "page_index": 1,
                    "vault_id": "test_vault_id",
                    "output_file": "510 - Test House/Main Category/Grouped Document.lnk",
                    "target_folder": "510 - Test House/Main Category"
                },
                {
                    "page_index": 2,
                    "vault_id": "test_vault_id",
                    "output_file": "510 - Test House/Main Category/Grouped Document.lnk",
                    "target_folder": "510 - Test House/Main Category"
                }
            ]
        }
    }
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(mock_state, f)
        
    args = DummyArgs(valid_house_dir)
    
    # Mock batch_read_shortcut_targets to bypass PowerShell flakiness
    with patch('src.utils.fs.batch_read_shortcut_targets') as mock_read, \
         patch('src.core.verification.batch_read_shortcut_targets') as mock_read_ver:
        # Override the dictionary so that .get() always returns the target vault_pdf
        mock_map = MagicMock()
        mock_map.get.return_value = os.path.abspath(str(vault_pdf))
        
        mock_read.return_value = mock_map
        mock_read_ver.return_value = {os.path.abspath(str(shortcut_path)): os.path.abspath(str(vault_pdf))}
        
        result = run_reconcile_mode(args)

    assert result == 0, "Reconciliation failed"
    
    # Reconciler renames the directory if the tenant changed
    new_state_file = tmp_path / "510 - mock" / ".source_files" / "510_state.json"
    
    # Verify that state.json STILL has 3 pages!
    with open(new_state_file, 'r', encoding='utf-8') as f:
        final_state = json.load(f)
        
    final_manifest = final_state.get("manifest", {}).get("per_page", [])
    
    # The regression deleted 2 pages. We assert all 3 pages are still there.
    assert len(final_manifest) == 3, f"Expected 3 pages, found {len(final_manifest)}. Regression occurred: Many-to-One pages were deleted."
