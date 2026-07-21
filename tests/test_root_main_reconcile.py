import pytest
from pathlib import Path
import json
import yaml
import shutil
from unittest.mock import patch, MagicMock

from src.main import run_reconcile_mode

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
        
    cleaned_data = [{
        "page_index": 0, 
        "canonical_tenant": "Ahmed Yousuf", 
        "resolved_date": "2021-05-11", 
        "topics": ["02_بيانات شخصية"], 
        "is_junk": False,
        "category": "personal",
        "content_explanation": "mock explanation",
        "original_index": 0
    }]
    with open(source_dir / f"{house_id}_1_cleaned.json", "w") as f:
        json.dump(cleaned_data, f)
        
    grouped_data = [{
        "start_page": 0, 
        "end_page": 0, 
        "primary_tenant": "Ahmed Yousuf", 
        "primary_topic": "02_بيانات شخصية", 
        "metadata": {"date": "2021-05-11"}, 
        "issues": [], 
        "language": "ar",
        "category": "personal",
        "dates": ["2021-05-11"]
    }]
    with open(source_dir / f"{house_id}_2_grouped.json", "w") as f:
        json.dump(grouped_data, f)
        
    routed_data = {
        "per_page": [
            {
                "page_index": 0,
                "tenant": "Ahmed Yousuf",
                "target_folder": "Ahmed Yousuf/02_بيانات شخصية",
                "output_file": f"{house_id} - Ahmed Yousuf/Ahmed Yousuf/02_بيانات شخصية/2021-05-11.pdf"
            }
        ]
    }
    with open(source_dir / f"{house_id}_3_routed_and_finalized.json", "w") as f:
        json.dump(routed_data, f)
        
    # Create the old PDF file
    old_pdf_path = tmp_path / f"{house_id} - Ahmed Yousuf/Ahmed Yousuf/02_بيانات شخصية/2021-05-11.pdf"
    old_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    old_pdf_path.touch()
    
    args = DummyArgs(target_dir=target_dir)
    
    # We patch FileOrganizer to avoid complicated real dependencies just to test the move logic
    with patch("src.timeline.core.FileOrganizer") as mock_org:
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
