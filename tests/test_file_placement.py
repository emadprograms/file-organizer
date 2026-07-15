import pytest
from pathlib import Path
import shutil
import logging
from src.main import run_generation_pass
from unittest.mock import patch, MagicMock

def test_file_placement_logic(tmp_path):
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    house_id = "test_house"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create mock categorized pdf
    pdf_path = target_dir / f"{house_id}_categorized.pdf"
    pdf_path.touch()
    
    # Create mock report json
    report_json = target_dir / f"{house_id}_report.json"
    report_json.touch()
    
    # Create .run_cache and mock checkpoints
    run_cache_dir = output_dir / ".run_cache"
    run_cache_dir.mkdir()
    cleaned_path = run_cache_dir / f"{house_id}_1_cleaned.json"
    cleaned_path.touch()
    grouped_path = run_cache_dir / f"{house_id}_2_grouped.json"
    grouped_path.touch()
    routed_path = run_cache_dir / f"{house_id}_3_routed_and_finalized.json"
    routed_path.touch()
    
    # Mock dependencies inside run_generation_pass
    # Simulate what organize() does: renames target_dir to house_dir
    house_dir = output_dir / house_id
    def organize_side_effect(*args, **kwargs):
        # organize() calls ensure_target_directories which renames target_dir -> house_dir
        if target_dir.exists() and not house_dir.exists():
            target_dir.rename(house_dir)
        return ([{"output_file": "mock_output.pdf"}], house_id)
    
    with patch('src.timeline.FileOrganizer') as MockOrganizer, \
         patch('src.timeline.run_reconciliation') as mock_reconciliation, \
         patch('src.main.fitz.open') as mock_fitz_open:
        
        mock_organizer_instance = MockOrganizer.return_value
        mock_organizer_instance.organize.side_effect = organize_side_effect
        
        mock_doc = MagicMock()
        mock_doc.page_count = 10
        mock_fitz_open.return_value.__enter__.return_value = mock_doc
        
        logger = logging.getLogger("test")
        
        run_generation_pass([], target_dir, house_id, output_dir, logger, dry_run=False)
        
    # Assertions
    source_files_dir = output_dir / house_id / ".source_files"
    assert source_files_dir.exists(), ".source_files directory should exist"
    
    # D-01: *_categorized.pdf is moved to house_dir and NOT into .source_files
    expected_pdf_path = output_dir / house_id / pdf_path.name
    assert expected_pdf_path.exists(), "Categorized PDF should be moved to house_dir"
    assert not (source_files_dir / pdf_path.name).exists(), "Categorized PDF should not be in .source_files"
    
    # D-03: *_report.json is correctly moved to .source_files/
    assert not report_json.exists(), "Report JSON should be moved from target_dir"
    assert (source_files_dir / report_json.name).exists(), "Report JSON should be in .source_files"
    
    # D-03: .run_cache checkpoints are correctly moved to .source_files/
    assert (source_files_dir / cleaned_path.name).exists(), "Cleaned checkpoint should be moved"
    assert (source_files_dir / grouped_path.name).exists(), "Grouped checkpoint should be moved"
    assert (source_files_dir / routed_path.name).exists(), "Routed checkpoint should be moved"
    assert not run_cache_dir.exists(), ".run_cache directory should be deleted"
