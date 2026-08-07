import json
from pathlib import Path
import pytest

from scripts.migrate_legacy_reports import migrate_house
from src.core.state import State
from src.utils.fs import create_shortcut

def test_migrate_house(tmp_path):
    house_dir = tmp_path / "123 - Test House"
    house_dir.mkdir()
    source_dir = house_dir / ".source_files"
    source_dir.mkdir()
    timeline_dir = house_dir / "[Timeline View]"
    timeline_dir.mkdir()
    
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    
    # Create old report
    old_report = source_dir / "123_report.json"
    old_report.write_text("[{\"old\": \"data\"}]")
    
    # Create state
    state_file = source_dir / "123_state.json"
    state_data = {
        "house_id": "123",
        "routed_documents": [
            {"vault_id": "v1", "dates": ["2020-01-01"], "brief_arabic_title": "Doc1", "start_page": 2},
            {"vault_id": "v2", "dates": ["2019-01-01"], "brief_arabic_title": "Doc2", "start_page": 1}
        ]
    }
    state_file.write_text(json.dumps(state_data))
    
    # Create vault targets
    (vault_dir / "doc_v1.pdf").touch()
    (vault_dir / "doc_v2.pdf").touch()
    
    # Create shortcuts in reverse order to test timeline chronological sorting
    # Timeline should sort alphabetically by name (which acts chronologically based on prefix)
    create_shortcut(str(vault_dir / "doc_v2.pdf"), str(timeline_dir / "001 - 2019-01-01 - Doc2.lnk"))
    create_shortcut(str(vault_dir / "doc_v1.pdf"), str(timeline_dir / "002 - 2020-01-01 - Doc1.lnk"))
    
    # Run migration
    success = migrate_house(house_dir, dry_run=False)
    assert success is True
    
    # Verify new report
    assert old_report.exists()
    new_data = json.loads(old_report.read_text())
    
    assert len(new_data) == 2
    # First should be v2
    assert new_data[0]["vault_id"] == "v2"
    assert new_data[0]["date"] == "2019-01-01"
    assert new_data[0]["timeline_name"] == "001 - 2019-01-01 - Doc2.lnk"
    
    # Second should be v1
    assert new_data[1]["vault_id"] == "v1"
    assert new_data[1]["date"] == "2020-01-01"
    assert new_data[1]["timeline_name"] == "002 - 2020-01-01 - Doc1.lnk"

def test_migrate_house_no_timeline(tmp_path):
    house_dir = tmp_path / "123 - Test House"
    house_dir.mkdir()
    source_dir = house_dir / ".source_files"
    source_dir.mkdir()
    
    old_report = source_dir / "123_report.json"
    old_report.write_text("[{\"old\": \"data\"}]")
    
    state_file = source_dir / "123_state.json"
    state_data = {
        "house_id": "123",
        "routed_documents": [
            {"vault_id": "v1", "dates": ["2020-01-01"], "brief_arabic_title": "Doc1", "start_page": 2},
            {"vault_id": "v2", "dates": ["2019-01-01"], "brief_arabic_title": "Doc2", "start_page": 1}
        ]
    }
    state_file.write_text(json.dumps(state_data))
    
    success = migrate_house(house_dir, dry_run=False)
    assert success is True
    
    new_data = json.loads(old_report.read_text())
    
    assert len(new_data) == 2
    # Should fallback to start_page order
    assert new_data[0]["vault_id"] == "v2" # start_page 1
    assert new_data[1]["vault_id"] == "v1" # start_page 2
    assert "timeline_name" not in new_data[0]
