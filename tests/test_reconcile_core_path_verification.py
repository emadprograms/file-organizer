import json
import pytest
from pathlib import Path
from unittest.mock import patch
from src.reconcile.core import run_reconcile_mode
# No unused imports

def test_reconcile_generates_correct_paths(tmp_path):
    """
    Test that reconcile_house generates output_file paths that match reality
    and use the correct tenant_folder (with date suffixes).
    """
    # 1. Setup mock workspace
    area_dir = tmp_path / "Safra C"
    house_id = "510"
    tenant_base = "علي مسعد حسين عبد الله"
    tenant_full = f"{tenant_base} ‎(2000 - الآن)‎"
    
    house_dir = area_dir / f"{house_id} - {tenant_base}"
    source_dir = house_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    # 2. Setup mock data
    yaml_data = [{
        "name": tenant_base,
        "start_date": "2000-01-01",
        "end_date": "present"
    }]
    with open(source_dir / f"{house_id}_1_tenants.yaml", "w", encoding='utf-8') as f:
        import yaml
        yaml.dump(yaml_data, f, allow_unicode=True)
        
    cleaned_data = [
        {"original_index": 0, "canonical_tenant": tenant_base, "category": "forms", "resolved_date": "2024-03-24", "content_explanation": "test"}
    ]
    with open(source_dir / f"{house_id}_1_cleaned.json", "w", encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False)
        
    grouped_data = [
        {"start_page": 0, "end_page": 0, "primary_tenant": tenant_base, "category": "forms", "dates": ["2024-03-24"]}
    ]
    with open(source_dir / f"{house_id}_2_grouped.json", "w", encoding='utf-8') as f:
        json.dump(grouped_data, f, ensure_ascii=False)
        
    routed_data = {
        "summary": {"total_input_pages": 1, "total_output_pages": 1, "output_file_count": 1},
        "per_page": [{
            "page_index": 0,
            "tenant": tenant_base,
            "date": "2024-03-24",
            "output_file": f"{house_id} - {tenant_base}/{tenant_base}/01_بيانات أساسية/2024-03-24.pdf",
            "page_in_output": 1,
            "target_folder": f"{tenant_base}/01_بيانات أساسية"
        }]
    }
    with open(source_dir / f"{house_id}_3_routed_and_finalized.json", "w", encoding='utf-8') as f:
        json.dump(routed_data, f, ensure_ascii=False)
        
    # Create the physical file using the old path so it can be moved
    old_file_path = house_dir / tenant_base / "01_بيانات أساسية" / "2024-03-24.pdf"
    old_file_path.parent.mkdir(parents=True, exist_ok=True)
    old_file_path.touch()
    
    # 3. Run reconcile
    class Args:
        target_dir = house_dir
        dry_run = False
    args = Args()
    
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        instance = mock_org.return_value
        instance.compute_tenant_folders.return_value = ({tenant_base: tenant_full}, tenant_full)
        run_reconcile_mode(args)
    
    # 4. Verify the new routed JSON paths
    new_routed_path = area_dir / f"{house_id} - {tenant_full}" / ".source_files" / f"{house_id}_3_routed_and_finalized.json"
    assert new_routed_path.exists(), "Reconcile did not move the .source_files directory to the new house folder correctly"
    
    with open(new_routed_path, "r", encoding='utf-8') as f:
        new_routed_data = json.load(f)
        
    per_page = new_routed_data["per_page"]
    assert len(per_page) == 1
    
    output_file = per_page[0]["output_file"]
    target_folder = per_page[0]["target_folder"]
    
    # Assert that the new paths explicitly contain the date suffix!
    expected_output_file = f"{house_id} - {tenant_full}/{tenant_full}/01_بيانات أساسية/2024-03-24.pdf"
    assert output_file == expected_output_file, f"Output file mismatch. Expected {expected_output_file}, got {output_file}"
    assert target_folder == f"{tenant_full}/01_بيانات أساسية"
    
    # Verify the physical file exists at the exact path specified by the JSON
    physical_file = area_dir / output_file
    assert physical_file.exists(), f"Physical file does not exist at the JSON specified path: {output_file}"
