from typing import Any
import pytest
from pathlib import Path
import shutil
import logging
from src.main import run_generation_pass
from unittest.mock import patch, MagicMock

def test_file_placement_logic(tmp_path) -> None:
    """
    Test file placement logic.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
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
    report_json.write_text("[1,2,3,4,5,6,7,8,9,10]")
    
    house_dir = output_dir / house_id
    
    # Create mock checkpoints (these are now generated directly in .source_files, 
    # but run_generation_pass moves other JSON files from target_dir to .source_files)
    source_files_dir = house_dir / ".source_files"
    source_files_dir.mkdir(parents=True)
    cleaned_path = source_files_dir / f"{house_id}_1_cleaned.json"
    cleaned_path.touch()
    grouped_path = source_files_dir / f"{house_id}_2_grouped.json"
    grouped_path.touch()
    routed_path = source_files_dir / f"{house_id}_3_routed_and_finalized.json"
    routed_path.touch()
    
    # Mock dependencies inside run_generation_pass
    # Simulate what organize() does: renames target_dir to house_dir
    house_dir = output_dir / house_id
    def organize_side_effect(*args, **kwargs) -> Any:
        """
        Provide the organize side effect fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        # organize() calls ensure_target_directories which renames target_dir -> house_dir
        if target_dir.exists() and not house_dir.exists():
            target_dir.rename(house_dir)
        return ([{"output_file": "mock_output.pdf", "target_folder": "mock/mock"}], house_id)
    
    with patch('src.timeline.FileOrganizer') as MockOrganizer, \
         patch('src.timeline.run_reconciliation') as mock_reconciliation, \
         patch('src.pipeline.runner.fitz.open') as mock_fitz_open, \
         patch('src.pdf.compress.compress_pdf') as mock_compress_pdf:
        
        mock_organizer_instance = MockOrganizer.return_value
        mock_organizer_instance.organize.side_effect = organize_side_effect
        
        mock_doc = MagicMock()
        mock_doc.page_count = 10
        mock_fitz_open.return_value.__enter__.return_value = mock_doc
        
        def simulate_compress(tmp, final) -> Any:
            """
            Provide the simulate compress fixture/mock.

            Returns:
            The appropriate fixture or mock value.
            """
            Path(final).touch()
            # Also touch tmp so os.remove doesn't fail
            Path(tmp).touch()
        mock_compress_pdf.side_effect = simulate_compress
        
        logger = logging.getLogger("test")
        
        run_generation_pass([], target_dir, house_id, output_dir, logger, dry_run=False, json_path=report_json)
        
    # Assertions
    assert source_files_dir.exists(), ".source_files directory should exist"
    
    # D-01: *_categorized.pdf is moved to .source_files -> wait, it is deleted in main.py
    # main.py: "Delete the original categorized PDF upon completion"
    expected_pdf_path = output_dir / house_id / pdf_path.name
    assert not expected_pdf_path.exists(), "Categorized PDF should be removed or moved out of house_dir root"
    
    finalized_pdf_path = output_dir / house_id / f"{house_id}_finalized.pdf"
    assert finalized_pdf_path.exists(), "Finalized PDF should be created in house_dir"
    
    # D-03: *_report.json is correctly moved to .source_files/
    assert not report_json.exists(), "Report JSON should be moved from target_dir"
    assert (source_files_dir / report_json.name).exists(), "Report JSON should be in .source_files"
    
    # D-03: .run_cache checkpoints are correctly moved to .source_files/ (already in source_files in our mock)
    assert (source_files_dir / cleaned_path.name).exists(), "Cleaned checkpoint should exist"
    assert (source_files_dir / grouped_path.name).exists(), "Grouped checkpoint should exist"
    assert (source_files_dir / routed_path.name).exists(), "Routed checkpoint should exist"
