import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import fitz

from src.watcher.orchestrator import FSUIOrchestrator
from src.timeline.core import FileOrganizer

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.inbox_path = "dummy/inbox"
    config.areas_root_path = "dummy/areas"
    return config

@pytest.fixture
def mock_llm_client():
    return MagicMock()

def create_dummy_pdf(path: Path, pages: int = 1):
    doc = fitz.open()
    for _ in range(pages):
        page = doc.new_page()
        page.insert_text(fitz.Point(50, 50), "Dummy page")
    doc.save(str(path))
    doc.close()

def test_ensure_target_dirs_prepend_mode_no_rename(tmp_path):
    organizer = FileOrganizer()
    
    target_dir = tmp_path / "temp_target"
    target_dir.mkdir()
    
    output_base = tmp_path / "areas"
    output_base.mkdir()
    house_dir = output_base / "502 - OldTenant"
    house_dir.mkdir()
    
    tenant_folders = {"Tenant": "Tenant_Folder"}
    
    # Run in append mode
    result_path = organizer.ensure_target_directories(
        target_dir=target_dir,
        tenant_folder_names=tenant_folders,
        full_house_id="502 - OldTenant",
        output_base_dir=output_base,
        prepend_mode=True
    )
    
    assert result_path == house_dir
    assert target_dir.exists() # Was not renamed
    assert (house_dir / "Tenant_Folder").exists()

@patch("src.watcher.orchestrator.run_generation_pass")
@patch("src.pdf.compress.compress_pdf")
@patch("src.watcher.orchestrator.shutil.copy")
def test_finalize_uses_existing_house_dir(mock_copy, mock_compress, mock_run_gen, tmp_path, mock_config, mock_llm_client):
    mock_config.areas_root_path = str(tmp_path / "areas")
    areas_root = Path(mock_config.areas_root_path)
    area_dir = areas_root / "Safra D"
    area_dir.mkdir(parents=True)
    
    house_dir = area_dir / "502 - OldTenant"
    house_dir.mkdir()
    
    source_files = house_dir / ".source_files"
    source_files.mkdir()
    
    # Create finalized PDF
    finalized_pdf = house_dir / "502_finalized.pdf"
    create_dummy_pdf(finalized_pdf, 1)
    
    # Setup routed JSON
    routed_json = source_files / "502_3_routed_and_finalized.json"
    with open(routed_json, "w", encoding="utf-8") as f:
        json.dump([
            {"start_page": 0, "end_page": 0, "primary_tenant": "OldTenant", "folder_path": "folder", "dates": ["2023"], "brief_arabic_title": "old", "category": "Unknown"}
        ], f)
        
    orchestrator = FSUIOrchestrator(mock_config, mock_llm_client)
    orchestrator.cache_dir = tmp_path / "cache"
    
    # Create a proposed OK pdf to finalize
    inbox_pdf = tmp_path / "inbox" / "Safra D 502 NewTenant G 2024 test OK.pdf"
    inbox_pdf.parent.mkdir(parents=True)
    create_dummy_pdf(inbox_pdf, 1)
    
    # Create temp cache dir
    tmp_dir = orchestrator.cache_dir / f".tmp_{inbox_pdf.name[:-7]} Proposed"
    tmp_dir.mkdir(parents=True)
    
    with open(tmp_dir / "_routed_prepend_mode.json", "w", encoding="utf-8") as f:
        json.dump([
            {"start_page": 0, "end_page": 0, "primary_tenant": "NewTenant", "folder_path": "folder", "dates": ["2024"], "brief_arabic_title": "new", "category": "Unknown"}
        ], f)
        
    # Mock compress_pdf to just copy the file so fitz doesn't complain
    def fake_compress(src, dst):
        import shutil
        shutil.copy(src, dst)
    mock_compress.side_effect = fake_compress

    # Run finalize
    orchestrator.finalize(inbox_pdf)
    
    # Verify new directory not created
    assert not (area_dir / "502 - NewTenant").exists()
    
    # Verify fixed_house_dir passed to run_generation_pass
    assert mock_run_gen.called
    kwargs = mock_run_gen.call_args[1]
    assert kwargs["fixed_house_dir"] == house_dir
    assert kwargs["target_dir"] == house_dir
    assert kwargs["house_id"] == "502"

@patch("src.watcher.orchestrator.run_generation_pass")
@patch("src.pdf.compress.compress_pdf")
def test_finalize_no_raw_append_created(mock_compress, mock_run_gen, tmp_path, mock_config, mock_llm_client):
    mock_config.areas_root_path = str(tmp_path / "areas")
    areas_root = Path(mock_config.areas_root_path)
    area_dir = areas_root / "Safra D"
    area_dir.mkdir(parents=True)
    
    house_dir = area_dir / "502 - OldTenant"
    house_dir.mkdir()
    
    source_files = house_dir / ".source_files"
    source_files.mkdir()
    
    finalized_pdf = house_dir / "502_finalized.pdf"
    create_dummy_pdf(finalized_pdf, 1)
    
    routed_json = source_files / "502_3_routed_and_finalized.json"
    with open(routed_json, "w", encoding="utf-8") as f:
        json.dump([
            {"start_page": 0, "end_page": 0, "primary_tenant": "OldTenant", "folder_path": "folder", "dates": ["2023"], "brief_arabic_title": "old", "category": "Unknown"}
        ], f)
        
    orchestrator = FSUIOrchestrator(mock_config, mock_llm_client)
    orchestrator.cache_dir = tmp_path / "cache"
    
    inbox_pdf = tmp_path / "inbox" / "Safra D 502 NewTenant G 2024 test OK.pdf"
    inbox_pdf.parent.mkdir(parents=True)
    create_dummy_pdf(inbox_pdf, 1)
    
    tmp_dir = orchestrator.cache_dir / f".tmp_{inbox_pdf.name[:-7]} Proposed"
    tmp_dir.mkdir(parents=True)
    
    with open(tmp_dir / "_routed_prepend_mode.json", "w", encoding="utf-8") as f:
        json.dump([
            {"start_page": 0, "end_page": 0, "primary_tenant": "NewTenant", "folder_path": "folder", "dates": ["2024"], "brief_arabic_title": "new", "category": "Unknown"}
        ], f)
        
    def fake_compress(src, dst):
        import shutil
        shutil.copy(src, dst)
    mock_compress.side_effect = fake_compress

    orchestrator.finalize(inbox_pdf)
    
    assert not (source_files / "502_raw_prepend.pdf").exists()
    assert not (house_dir / "502_raw_prepend.pdf").exists()


