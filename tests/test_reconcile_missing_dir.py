import pytest
import os
import shutil
import json
from pathlib import Path
from src.reconcile.core import run_reconcile_mode


def test_reconcile_abort_on_missing_dir(tmp_path):
    """
    Test that running reconciliation on a non-existent directory immediately aborts
    and does NOT wipe the state. This prevents the catastrophic bug where a missing
    directory is interpreted as 'the user deleted all files' resulting in a full vault wipe.
    """
    
    # 1. Setup a valid mock state file in a safe location
    valid_house_dir = tmp_path / "123 - Test House"
    source_dir = valid_house_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    # Create mock state with 1 page
    state_file = source_dir / "123_state.json"
    mock_state = {
        "version": "5.0",
        "house_id": "123",
        "routed_documents": {
            "per_page": [
                {
                    "page_index": 1,
                    "vault_id": "test_vault_id",
                    "output_file": "01_Category/doc.lnk"
                }
            ]
        }
    }
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(mock_state, f)
        
    # We will pass a non-existent path to run_reconcile_mode
    non_existent_dir = tmp_path / "123 - Non Existent House"
    
    # Mock args
    class DummyArgs:
        target_dir = non_existent_dir
        dry_run = False
        
    args = DummyArgs()
    
    # 2. Execute reconciliation
    # The reconciler should return 1 (error code) and not crash or wipe anything
    result = run_reconcile_mode(args)
    
    # Assert it returns error code 1
    assert result == 1, "Reconciler should return 1 when target_dir does not exist."
    
    # Assert the state file was not touched/corrupted by a side-effect
    assert state_file.exists(), "State file must not be deleted."
    with open(state_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data["routed_documents"]["per_page"]) == 1, "State manifest must not be wiped out!"
        
    # Also verify that no .source_files/.trash directory was created inside the non-existent dir
    assert not (non_existent_dir / ".source_files").exists(), "Reconciler should not create .source_files in a non-existent directory."
