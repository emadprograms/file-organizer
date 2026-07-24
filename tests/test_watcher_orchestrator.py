import pytest
import os
import time
from pathlib import Path
import unittest.mock
from unittest.mock import MagicMock, patch

from src.watcher.orchestrator import FSUIOrchestrator
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
    
    with patch("src.watcher.orchestrator.parse_filename_syntax", create=True) as mock_parse, \
         patch("src.watcher.orchestrator.infer_missing_data", create=True) as mock_infer, \
         patch("src.watcher.orchestrator.resolve_area", return_value="Area1", create=True), \
         patch("src.watcher.orchestrator.resolve_tenant", return_value="Smith", create=True), \
         patch("src.watcher.orchestrator.Pipeline", create=True) as mock_pipeline_cls:
        
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
        from src.core.schemas import DocumentGroup
        doc_group = DocumentGroup(
            start_page=0, end_page=0, primary_tenant="Smith",
            category="01_Test", dates=["2023-01-01"],
            brief_arabic_title="Invoice", folder_path="01_Test"
        )
        mock_pipeline._route_documents.return_value = [doc_group]
        
        with patch.dict('sys.modules', {'fitz': MagicMock()}):
            mock_fitz = __import__('sys').modules['fitz']
            mock_doc = MagicMock()
            mock_doc.__enter__.return_value = mock_doc
            mock_doc.page_count = 1
            def mock_save(path, *args, **kwargs):
                Path(path).touch()
            mock_doc.save.side_effect = mock_save
            mock_fitz.open.return_value = mock_doc
            
            def mock_process_unclassified(master_tmp_dir, *args, **kwargs):
                (master_tmp_dir / f"{test_file.stem}_report.json").write_text("[]")
                
            with patch("src.watcher.orchestrator.process_unclassified_pdf", side_effect=mock_process_unclassified):
                orchestrator.propose(test_file)
        
    expected_name = "Area1 123 Smith G 2023-01-01 Invoice_Proposed.pdf"
    assert (inbox / expected_name).exists()
    assert not test_file.exists()
    
    # Assert temp dir was created for the proposed file
    expected_tmp_dir = inbox / ".tmp_Area1 123 Smith G 2023-01-01 Invoice_Proposed"
    assert expected_tmp_dir.exists()

def test_propose_handles_errors(mock_config, mock_llm):
    orchestrator = FSUIOrchestrator(mock_config, mock_llm)
    
    inbox = Path(mock_config.inbox_path)
    test_file = inbox / "bad.pdf"
    test_file.touch()
    
    with patch("src.watcher.orchestrator.parse_filename_syntax", side_effect=ValueError("Bad format"), create=True):
        orchestrator.propose(test_file)
        
    assert (inbox / "bad_Error_Invalid_Format.pdf").exists()
    assert not test_file.exists()

def test_finalize_moves_and_invokes_pipeline(mock_config, mock_llm):
    orchestrator = FSUIOrchestrator(mock_config, mock_llm)
    
    inbox = Path(mock_config.inbox_path)
    clean_name = "Area1 123 Smith 2023-01-01 Invoice"
    test_file = inbox / f"{clean_name} OK.pdf"
    test_file.write_bytes(b"%PDF-1.4 fake content")
    
    tmp_dir = inbox / f".tmp_{clean_name}"
    tmp_dir.mkdir()
    
    import hashlib
    hasher = hashlib.sha256()
    with open(test_file, 'rb') as f:
        hasher.update(f.read())
    file_hash = hasher.hexdigest()
    (tmp_dir / "pdf_hash.txt").write_text(file_hash)
    
    import json
    routed_data = [{
        "start_page": 0, "end_page": 0,
        "primary_tenant": "Smith", "category": "Test",
        "dates": ["2023-01-01"], "brief_arabic_title": "Invoice",
        "folder_path": "01_Test"
    }]
    (tmp_dir / "_routed_append_mode.json").write_text(json.dumps(routed_data))
    
    house_dir = Path(mock_config.areas_root_path) / "Area1" / "123"
    house_dir.mkdir(parents=True, exist_ok=True)
    source_files_dir = house_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    (source_files_dir / "123_1_cleaned.json").write_text("[]")
    
    # Build a mock fitz module that handles all the fitz.open() calls
    mock_fitz = MagicMock()
    mock_doc = MagicMock()
    mock_doc.__enter__ = MagicMock(return_value=mock_doc)
    mock_doc.__exit__ = MagicMock(return_value=False)
    mock_doc.page_count = 1
    def mock_save(path, *args, **kwargs):
        Path(path).touch()
    mock_doc.save = MagicMock(side_effect=mock_save)
    mock_fitz.open.return_value = mock_doc
    
    with patch.dict('sys.modules', {'fitz': mock_fitz}), \
         patch("src.watcher.orchestrator.run_generation_pass") as mock_generation, \
         patch("src.pdf.compress.compress_pdf"):
        
        orchestrator.finalize(test_file)
        
        # After finalize, the tmp_dir should be deleted
        assert not tmp_dir.exists()
        
        # And the test_file should be deleted
        assert not test_file.exists()
        
        # And the generation pass should be called
        mock_generation.assert_called_once()

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
