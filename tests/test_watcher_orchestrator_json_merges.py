import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import fitz

from src.watcher.orchestrator import FSUIOrchestrator

@patch("src.watcher.orchestrator.time.sleep")
@patch("src.watcher.orchestrator.run_generation_pass")
@patch("src.watcher.orchestrator.shutil")
@patch("src.watcher.orchestrator.os.remove")
def test_orchestrator_json_merge_bugfixes(mock_remove, mock_shutil, mock_rgp, mock_sleep, tmp_path):
    """
    Tests Bug 1 (dict to list report conversion) and Bug 2 (routed JSON prepend).
    """
    mock_config = MagicMock()
    mock_config.inbox_path = tmp_path / "inbox"
    mock_config.areas_root_path = tmp_path / "areas"
    
    orchestrator = FSUIOrchestrator(mock_config, MagicMock())
    orchestrator.cache_dir = tmp_path / "cache"
    orchestrator.cache_dir.mkdir(parents=True)
    
    inbox_pdf = orchestrator.cache_dir / "testArea 1273 - test House OK.pdf"
    
    # 1. Setup the House folder structure
    areas_root = mock_config.areas_root_path
    house_dir = areas_root / "testArea" / "1273 - test House"
    source_files = house_dir / ".source_files"
    source_files.mkdir(parents=True)
    
    # 2. Setup master JSONs (.source_files)
    # Bug 1 setup: Old report is a DICT
    old_report = {
        "1": {"status": "classified", "category": "forms", "original_index": 0},
        "2": {"status": "classified", "category": "letters", "original_index": 1}
    }
    with open(source_files / "1273_report.json", "w") as f:
        json.dump(old_report, f)
        
    # Bug 2 setup: Master routed is a dict with per_page
    old_routed = {
        "summary": {"total": 2},
        "per_page": [
            {"page_index": 0, "output_file": "doc1.pdf"},
            {"page_index": 1, "output_file": "doc2.pdf"}
        ]
    }
    with open(source_files / "1273_3_routed_and_finalized.json", "w") as f:
        json.dump(old_routed, f)
        
    # Create empty cleaned/grouped so they don't crash
    with open(source_files / "1273_1_cleaned.json", "w") as f:
        json.dump([], f)
    with open(source_files / "1273_2_grouped.json", "w") as f:
        json.dump([], f)
        
    # Mock the fitz PDF reading inside merge_json
    doc = fitz.open()
    doc.new_page() # 1 page addition
    doc.save(str(inbox_pdf))
    doc.close()
    
    # 3. Setup tmp_master JSONs (The new additions)
    import hashlib
    pdf_hash = hashlib.sha256(inbox_pdf.read_bytes()).hexdigest() if inbox_pdf.exists() else ""
    tmp_dir = orchestrator.cache_dir / ".tmp_testArea 1273 - test House Proposed"
    tmp_dir.mkdir(parents=True)
    with open(tmp_dir / "metadata.json", "w") as f:
        json.dump({"clean_name": "testArea 1273 - test House", "pdf_hash": pdf_hash}, f)
        
    new_report = [
        {"status": "classified", "category": "forms"}
    ]
    with open(tmp_dir / "_report_prepend_mode.json", "w") as f:
        json.dump(new_report, f)
        
    new_routed = [
        {
            "start_page": 0,
            "end_page": 0,
            "category": "forms",
            "dates": ["2025-01-01"],
            "primary_tenant": "OK",
            "page_index": 0, 
            "output_file": "new_add.pdf"
        }
    ]
    with open(tmp_dir / "_routed_prepend_mode.json", "w") as f:
        json.dump(new_routed, f)
        
    with open(tmp_dir / "_cleaned_prepend_mode.json", "w") as f:
        json.dump([], f)
    with open(tmp_dir / "_grouped_prepend_mode.json", "w") as f:
        json.dump([], f)

    # Mock parse_filename_syntax to return an object with tenant_hint
    mock_parsed_cmd = MagicMock()
    mock_parsed_cmd.tenant_hint = "OK"
    mock_parsed_cmd.group = "U"
    mock_parsed_cmd.date = None
    mock_parsed_cmd.title = None
    with patch("src.watcher.orchestrator.parse_filename_syntax", return_value=mock_parsed_cmd):
        with patch("src.watcher.orchestrator.resolve_area", return_value="testArea"):
            # Mock fitz so that house_dir_scan finds the directory containing .source_files
            orchestrator.finalize(inbox_pdf)
        
    # 4. Verify fixes
    with open(source_files / "1273_report.json", "r") as f:
        final_report = json.load(f)
        
    assert isinstance(final_report, list), "Bug 1 Failed: report JSON was not converted to list"
    assert len(final_report) == 3, f"Bug 1 Failed: expected 3 items, got {len(final_report)}. Old items were overwritten!"
    
    # Bug 2 Fix Verification: FSUIOrchestrator should NOT manually touch _3_routed_and_finalized.json
    # It delegates this to run_generation_pass using prepend_manifest=True
    with open(source_files / "1273_3_routed_and_finalized.json", "r") as f:
        final_routed = json.load(f)
    
    assert len(final_routed["per_page"]) == 2, "FSUIOrchestrator should not manually merge the routed JSON anymore"
    
    # Assert run_generation_pass was called with prepend_manifest=True
    mock_rgp.assert_called_once()
    kwargs = mock_rgp.call_args.kwargs
    assert kwargs.get("prepend_manifest") is True, "Bug 2 Failed: run_generation_pass must be called with prepend_manifest=True"
    
