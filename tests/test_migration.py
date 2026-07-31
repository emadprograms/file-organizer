import os
import json
import shutil
from pathlib import Path
from src.migration.v5_migration import migrate_to_v5

def test_migrate_v4_to_v5(tmp_path: Path):
    # Setup v4 structure
    house_dir = tmp_path / "101 - John Doe"
    house_dir.mkdir()
    
    tenant_dir = house_dir / "John Doe"
    tenant_dir.mkdir()
    
    category_dir = tenant_dir / "10_صيانة"
    category_dir.mkdir()
    
    # physical pdf
    pdf_path = category_dir / "2023-01-01 - test.pdf"
    pdf_path.write_text("dummy pdf content")
    
    # .source_files
    source_dir = house_dir / ".source_files"
    source_dir.mkdir()
    
    state_file = source_dir / "101_3_routed.json"
    state_file.write_text(json.dumps({
        "per_page": [
            {
                "page_index": 0,
                "output_file": "101 - John Doe/John Doe/10_صيانة/2023-01-01 - test.pdf",
                "dates": ["2023-01-01"],
                "brief_arabic_title": "test"
            }
        ]
    }))
    
    # Run migration (dry-run first)
    res = migrate_to_v5(house_dir, dry_run=True)
    assert res == 0
    assert pdf_path.exists()
    assert not pdf_path.with_suffix('.lnk').exists()
    
    # Run real migration
    res = migrate_to_v5(house_dir, dry_run=False)
    assert res == 0
    
    # Assertions
    assert not pdf_path.exists()
    assert pdf_path.with_suffix('.lnk').exists()
    
    vault_dir = source_dir / "vault"
    assert vault_dir.exists()
    vault_files = list(vault_dir.glob("*.pdf"))
    assert len(vault_files) == 1
    
    # Check new state
    new_state_file = source_dir / "101_3_routed_and_finalized.json"
    assert new_state_file.exists()
    assert not state_file.exists()
    
    with open(new_state_file) as f:
        data = json.load(f)
        p = data["per_page"][0]
        assert p.get("vault_id") is not None
        assert p.get("user_locked") is True
        assert p["output_file"] == "101 - John Doe/John Doe/10_صيانة/2023-01-01 - test.lnk"
        
    # Check timeline
    timeline_dir = house_dir / "00_Timeline_View"
    assert timeline_dir.exists()
    assert (timeline_dir / "001_test.lnk").exists()
