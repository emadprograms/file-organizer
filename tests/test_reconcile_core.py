import pytest
from pathlib import Path
import json
import yaml
import shutil
from unittest.mock import patch, MagicMock

from src.reconcile.core import run_reconcile_mode

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"

def test_run_reconcile_mode(tmp_path):
    # Setup mock house structure
    house_id = "504"
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [
        {"name": "Ahmed Yusuf Muraisil", "start_date": "2021-01-01", "end_date": "present"}
    ]
    with open(source_dir / f"{house_id}_tenants.yaml", "w") as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [{
            "page_index": 0, 
            "canonical_tenant": "Ahmed Yousuf", 
            "resolved_date": "2021-05-11", 
            "topics": ["02_بيانات شخصية"], 
            "is_junk": False,
            "category": "personal",
            "content_explanation": "mock explanation",
            "original_index": 0
        }],
        "grouped_documents": [{
            "start_page": 0, 
            "end_page": 0, 
            "primary_tenant": "Ahmed Yousuf", 
            "primary_topic": "02_بيانات شخصية", 
            "metadata": {"date": "2021-05-11"}, 
            "issues": [], 
            "language": "ar",
            "category": "personal",
            "dates": ["2021-05-11"]
        }],
        "manifest": {
            "per_page": [
                {
                    "page_index": 0,
                    "tenant": "Ahmed Yousuf",
                    "target_folder": "Ahmed Yousuf/02_بيانات شخصية",
                    "output_file": f"{house_id} - Ahmed Yousuf/Ahmed Yousuf/02_بيانات شخصية/2021-05-11.pdf"
                }
            ]
        }
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    # Create the old PDF file
    old_pdf_path = tmp_path / f"{house_id} - Ahmed Yousuf/Ahmed Yousuf/02_بيانات شخصية/2021-05-11.pdf"
    old_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    old_pdf_path.touch()
    
    args = DummyArgs(target_dir=target_dir)
    
    # We patch FileOrganizer to avoid complicated real dependencies just to test the move logic
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Ahmed Yusuf Muraisil": "Ahmed Yusuf Muraisil (2021 - الآن)"}, "Ahmed Yusuf Muraisil (2021 - الآن)")
        
        result = run_reconcile_mode(args)
    
    assert result == 0, "Reconcile mode should succeed"
    
    # Check that the file was moved to the new location
    new_house_dir = tmp_path / f"{house_id} - Ahmed Yusuf Muraisil (2021 - الآن)"
    assert new_house_dir.exists(), "New house directory should be created"
    
    expected_new_pdf = new_house_dir / "Ahmed Yusuf Muraisil (2021 - الآن)/02_بيانات شخصية/2021-05-11.pdf"
    assert expected_new_pdf.exists(), "New PDF should exist"
    
    # The old PDF should be gone
    assert not old_pdf_path.exists(), "Old PDF should have been moved"
    
    # Check that .source_files was moved
    assert (new_house_dir / ".source_files").exists(), "The .source_files directory should have been moved"
    assert not source_dir.exists(), "The old .source_files directory should no longer exist"
    
    # Check that the old house directories were removed
    assert not target_dir.exists(), "The old target_dir should have been removed"
    old_house_dir = tmp_path / f"{house_id} - Ahmed Yousuf"
    assert not old_house_dir.exists(), "The old house directory should have been removed"


def test_run_reconcile_mode_ghost_folders(tmp_path):
    """Test that reconciliation correctly cleans up old directories even when files collide or exist."""
    house_id = "514"
    target_dir = tmp_path / f"{house_id} - Old Tenant"
    new_house_dir = tmp_path / f"{house_id} - New Tenant (2024 - present)"
    
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [{"name": "New Tenant", "start_date": "2024-01-01", "end_date": "present"}]
    with open(source_dir / f"{house_id}_tenants.yaml", "w") as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [{"page_index": 0, "canonical_tenant": "Old Tenant", "resolved_date": "2024-05-11", "topics": ["02"], "is_junk": False, "category": "personal", "content_explanation": "", "original_index": 0}],
        "grouped_documents": [{"start_page": 0, "end_page": 0, "primary_tenant": "Old Tenant", "primary_topic": "02", "metadata": {"date": "2024-05-11"}, "issues": [], "language": "ar", "category": "personal", "dates": ["2024-05-11"]}],
        "manifest": {"per_page": [{"page_index": 0, "tenant": "Old Tenant", "target_folder": "Old/02", "output_file": f"{house_id} - Old Tenant/Old/02/test.pdf"}]}
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    # Create the old structure with a leftover root file (to trigger ghost folder issue)
    (target_dir / "dummy_root_file.txt").write_text("old text")
    
    # Pre-create the new directory and collide the root file
    new_house_dir.mkdir(parents=True)
    (new_house_dir / "dummy_root_file.txt").write_text("new text")
    
    args = DummyArgs(target_dir=target_dir)
    
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"New Tenant": "New Tenant (2024 - present)"}, "New Tenant (2024 - present)")
        
        result = run_reconcile_mode(args)
    
    assert result == 0
    assert not target_dir.exists(), "The ghost directory was not completely merged and removed!"
    assert (new_house_dir / "dummy_root_file.txt").read_text() == "new text" or (new_house_dir / "dummy_root_file.txt").read_text() == "old text"
    assert (new_house_dir / ".source_files").exists()

def test_run_reconcile_timeline_generation(tmp_path):
    """Test that reconciliation correctly infers missing vault_id and generates Timeline View."""
    house_id = "548"
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [{"name": "Test Tenant", "start_date": "2021-01-01", "end_date": "present"}]
    with open(source_dir / f"{house_id}_tenants.yaml", "w") as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [{"page_index": 0, "canonical_tenant": "Test Tenant", "resolved_date": "2021-05-11", "topics": ["02"], "is_junk": False, "category": "personal", "content_explanation": "", "original_index": 0}],
        # NO vault_id in grouped_documents (simulating legacy bug)
        "grouped_documents": [{"start_page": 0, "end_page": 0, "primary_tenant": "Test Tenant", "primary_topic": "02", "metadata": {"date": "2021-05-11"}, "issues": [], "language": "ar", "category": "personal", "dates": ["2021-05-11"]}],
        # vault_id exists in per_page
        "manifest": {"per_page": [{"page_index": 0, "tenant": "Test Tenant", "target_folder": "Test/02", "output_file": f"{house_id} - Test House/Test/02/test.pdf", "vault_id": "test_vault_id"}]}
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    old_pdf_path = tmp_path / f"{house_id} - Test House/Test/02/test.pdf"
    old_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    old_pdf_path.touch()
    
    args = DummyArgs(target_dir=target_dir)
    
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Test Tenant": "Test Tenant (2021 - الآن)"}, "Test Tenant (2021 - الآن)")
        
        result = run_reconcile_mode(args)
    
    assert result == 0
    new_house_dir = tmp_path / f"{house_id} - Test Tenant (2021 - الآن)"
    timeline_dir = new_house_dir / "[Timeline View]"
    assert timeline_dir.exists(), "Timeline View folder should be generated"
    
    timeline_shortcuts = list(timeline_dir.glob("*.lnk"))
    assert len(timeline_shortcuts) == 1, f"Expected 1 timeline shortcut, found {len(timeline_shortcuts)}"
