import pytest
import os
import time
from pathlib import Path
import unittest.mock
from unittest.mock import MagicMock, patch

from src.fs_ui.orchestrator import FSUIOrchestrator
from src.core.config import AppConfig

@pytest.fixture
def mock_config(tmp_path):
    inbox = tmp_path / "inbox"
    areas = tmp_path / "areas"
    inbox.mkdir()
    areas.mkdir()
    return AppConfig(
        inbox_path=str(inbox),
        areas_root_path=str(areas),
        area_mappings={}
    )

@pytest.fixture
def mock_llm():
    return MagicMock()

def test_process_inbox_delays_processing_if_size_unstable(mock_config, mock_llm):
    orchestrator = FSUIOrchestrator(mock_config, mock_llm)
    
    inbox = Path(mock_config.inbox_path)
    test_file = inbox / "test.pdf"
    test_file.write_text("initial")
    
    # Mock os.path.getsize to return changing sizes
    sizes = [7, 14, 14]
    
    def mock_getsize(path):
        if sizes:
            return sizes.pop(0)
        return 14
        
    class StopLoop(Exception):
        pass

    with patch("os.path.getsize", side_effect=mock_getsize), \
         patch("time.sleep", side_effect=[None, StopLoop]), \
         patch.object(orchestrator, "propose") as mock_propose:
        
        try:
            orchestrator.process_inbox()
        except StopLoop:
            pass
            
        # It must call propose once the size is stable (which we didn't reach due to StopLoop, 
        # actually let's make it reach stable size)
    
    sizes = [7, 14, 14] # Reset
    with patch("os.path.getsize", side_effect=mock_getsize), \
         patch("time.sleep", side_effect=[None, None, StopLoop]), \
         patch.object(orchestrator, "propose") as mock_propose:
        
        try:
            orchestrator.process_inbox()
        except StopLoop:
            pass
            
        mock_propose.assert_called_once_with(test_file)

def test_propose_renames_valid_file(mock_config, mock_llm):
    orchestrator = FSUIOrchestrator(mock_config, mock_llm)
    
    inbox = Path(mock_config.inbox_path)
    test_file = inbox / "123 smith.pdf"
    test_file.touch()
    
    # Setup area and house dirs, and tenant yaml to bypass new checks
    areas_root = Path(mock_config.areas_root_path)
    house_dir = areas_root / "Area1" / "123"
    house_dir.mkdir(parents=True)
    (house_dir / ".source_files").mkdir()
    (house_dir / ".source_files" / "123_tenants.yaml").touch()
    
    with patch("src.fs_ui.orchestrator.parse_filename_syntax", create=True) as mock_parse, \
         patch("src.fs_ui.orchestrator.infer_missing_data", create=True) as mock_infer, \
         patch("src.fs_ui.orchestrator.resolve_area", return_value="Area1", create=True), \
         patch("src.fs_ui.orchestrator.resolve_tenant", return_value="Smith", create=True), \
         patch("src.fs_ui.orchestrator.process_unclassified_pdf", create=True), \
         patch("src.fs_ui.orchestrator.Pipeline", create=True) as mock_pipeline_cls:
        
        mock_cmd = MagicMock()
        mock_cmd.house = "123"
        mock_cmd.tenant_hint = "smith"
        mock_cmd.group = "U"
        mock_cmd.date = "2023-01-01"
        mock_cmd.title = "Invoice"
        mock_parse.return_value = mock_cmd
        
        mock_infer.return_value = {
            "expected_house_number": "123",
            "tenant_hint": "Smith",
            "document_date": "2023-01-01",
            "document_type": "Invoice"
        }
        
        # Mock pipeline instance
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_pipeline._clean_documents.return_value = ([], None)
        mock_pipeline._group_documents.return_value = []
        mock_pipeline._route_documents.return_value = []
        
        orchestrator.propose(test_file)
        
    expected_name = "Area1 123 Smith U 2023-01-01 Invoice_Proposed.pdf"
    assert (inbox / expected_name).exists()
    assert not test_file.exists()
    
    # Assert temp dir was renamed correctly
    expected_tmp_dir = inbox / f".tmp_Area1 123 Smith U 2023-01-01 Invoice"
    assert expected_tmp_dir.exists()

def test_propose_handles_errors(mock_config, mock_llm):
    orchestrator = FSUIOrchestrator(mock_config, mock_llm)
    
    inbox = Path(mock_config.inbox_path)
    test_file = inbox / "bad.pdf"
    test_file.touch()
    
    with patch("src.fs_ui.orchestrator.parse_filename_syntax", side_effect=ValueError("Bad format"), create=True):
        orchestrator.propose(test_file)
        
    assert (inbox / "bad_Error_Invalid_Format.pdf").exists()
    assert not test_file.exists()

def test_finalize_moves_and_invokes_pipeline(mock_config, mock_llm):
    orchestrator = FSUIOrchestrator(mock_config, mock_llm)
    
    inbox = Path(mock_config.inbox_path)
    test_file = inbox / "Area1 123 Smith 2023-01-01 Invoice OK.pdf"
    test_file.touch()
    
    house_dir = Path(mock_config.areas_root_path) / "Area1" / "123"
    house_dir.mkdir(parents=True, exist_ok=True)
    
    # We need to mock the pipeline passes
    with patch("src.fs_ui.orchestrator.process_unclassified_pdf", create=True) as mock_unclass, \
         patch("src.fs_ui.orchestrator.run_cleaning_pass", return_value=([], None), create=True) as mock_clean, \
         patch("src.fs_ui.orchestrator.run_grouping_pass", return_value=[], create=True) as mock_group, \
         patch("src.fs_ui.orchestrator.run_routing_pass", return_value=[], create=True) as mock_route, \
         patch("src.fs_ui.orchestrator.run_generation_pass", create=True) as mock_gen:
        
        orchestrator.finalize(test_file)
        
        house_dir = Path(mock_config.areas_root_path) / "Area1" / "123"
        dest_pdf = house_dir / ".source_files" / "Area1 123 Smith 2023-01-01 Invoice.pdf"
        
        assert dest_pdf.exists()
        assert not test_file.exists()
        
        mock_unclass.assert_called_once()
        mock_clean.assert_called_once()
        mock_group.assert_called_once()
        mock_gen.assert_called_once_with(
            [], dest_pdf.parent, "123", house_dir, 
            unittest.mock.ANY, False, yaml_data=None, pdf_path=dest_pdf
        )

def test_orphan_cleanup(tmp_path):
    config = MagicMock()
    config.inbox_path = str(tmp_path)
    orch = FSUIOrchestrator(config, None)
    
    # Create an old orphan temp dir
    old_orphan = tmp_path / ".tmp_old"
    old_orphan.mkdir()
    os.utime(old_orphan, (time.time() - 400, time.time() - 400))
    
    # Create a new orphan temp dir
    new_orphan = tmp_path / ".tmp_new"
    new_orphan.mkdir()
    os.utime(new_orphan, (time.time() - 100, time.time() - 100))
    
    # Create an old temp dir with a matching PDF
    old_with_pdf = tmp_path / ".tmp_has_pdf"
    old_with_pdf.mkdir()
    os.utime(old_with_pdf, (time.time() - 400, time.time() - 400))
    (tmp_path / "has_pdf.pdf").touch()
    
    # Run process_inbox but break the loop
    original_sleep = time.sleep
    def fake_sleep(secs):
        raise StopIteration("Stop the loop")
    
    try:
        time.sleep = fake_sleep
        orch.process_inbox()
    except StopIteration:
        pass
    finally:
        time.sleep = original_sleep
        
    assert not old_orphan.exists()
    assert new_orphan.exists()
    assert old_with_pdf.exists()
