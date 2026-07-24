import pytest
import os
import shutil
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.watcher.orchestrator import FSUIOrchestrator
from src.core.config import AppConfig
from src.core.schemas import DocumentGroup

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "golden_1273"
MOCK_INBOX_DIR = FIXTURE_DIR / "mock_inbox"
EXPECTED_OUTPUT_DIR = FIXTURE_DIR / "expected_output"

@pytest.fixture
def mock_config():
    return AppConfig(
        inbox_path=str(MOCK_INBOX_DIR),
        areas_root_path=str(EXPECTED_OUTPUT_DIR),
        area_mappings={}
    )

@pytest.fixture
def mock_llm():
    return MagicMock()

def test_mock_append_propose(mock_config, mock_llm):
    # Setup the test file
    test_pdf = MOCK_INBOX_DIR / "mock_deduction.pdf"
    
    # Create required yaml
    house_dir = EXPECTED_OUTPUT_DIR / "1273" / "1273 - يونس محمد ملاك"
    house_dir.mkdir(parents=True, exist_ok=True)
    source_files_dir = house_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    (source_files_dir / "1273_1_tenants.yaml").touch(exist_ok=True)
    
    orchestrator = FSUIOrchestrator(mock_config, mock_llm)

    with patch("src.watcher.orchestrator.parse_filename_syntax", create=True) as mock_parse, \
         patch("src.watcher.orchestrator.infer_missing_data", create=True) as mock_infer, \
         patch("src.watcher.orchestrator.resolve_area", return_value="1273", create=True), \
         patch("src.watcher.orchestrator.resolve_tenant", return_value="يونس محمد ملاك", create=True), \
         patch("src.watcher.orchestrator.Pipeline", create=True) as mock_pipeline_cls:
        
        mock_cmd = MagicMock()
        mock_cmd.house = "1273"
        mock_cmd.tenant_hint = "يونس محمد ملاك"
        mock_cmd.group = "U"
        mock_cmd.date = "2006-04-18"
        mock_cmd.title = "استقطاع الإيجار الشهري للمتقاعدين"
        mock_parse.return_value = mock_cmd
        
        mock_infer.return_value = {
            "expected_house_number": "1273",
            "tenant_hint": "يونس محمد ملاك",
            "document_date": "2006-04-18",
            "document_type": "استقطاع الإيجار الشهري للمتقاعدين"
        }
        
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_pipeline._clean_documents.return_value = ([], None)
        mock_pipeline._group_documents.return_value = []
        
        # We need to return a DocumentGroup so the routing succeeds and creates a file
        doc_group = DocumentGroup(
            start_page=0,
            end_page=0,
            primary_tenant="يونس محمد ملاك",
            category="07_استقطاع إيجار",
            dates=["2006-04-18"],
            brief_arabic_title="استقطاع الإيجار الشهري للمتقاعدين",
            folder_path="07_استقطاع إيجار"
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
                (master_tmp_dir / f"{test_pdf.stem}_report.json").write_text("[]")
            
            with patch("src.watcher.orchestrator.process_unclassified_pdf", side_effect=mock_process_unclassified):
                orchestrator.propose(test_pdf)

    # Note: the group string depends on folder_name routing. If not mocked, it might fall back to 'G'
    expected_name = "1273 1273 يونس محمد ملاك G 2006-04-18 استقطاع الإيجار الشهري للمتقاعدين_Proposed.pdf"
    assert (MOCK_INBOX_DIR / expected_name).exists(), "The _Proposed file was not created"
    assert not test_pdf.exists(), "The original unclassified file was not removed"

def test_mock_append_finalize(mock_config, mock_llm):
    # Setup for finalize
    clean_name = "1273 1273 يونس محمد ملاك 09 2007-09-02 إخلاء الوحدات الإسكانية التابعة لوزارة الداخلية"
    test_file = MOCK_INBOX_DIR / f"{clean_name} OK.pdf"
    
    # Copy a real PDF instead of touching to avoid fitz errors
    shutil.copy(MOCK_INBOX_DIR / "mock_notice.pdf", test_file)
    
    tmp_dir = MOCK_INBOX_DIR / f".tmp_{clean_name}"
    tmp_dir.mkdir(exist_ok=True)
    
    # Needs a hash file to match
    import hashlib
    hasher = hashlib.sha256()
    with open(test_file, 'rb') as f:
        hasher.update(f.read())
    file_hash = hasher.hexdigest()
    
    (tmp_dir / "pdf_hash.txt").write_text(file_hash)
    (tmp_dir / "_routed_append_mode.json").write_text("[]")
    
    house_dir = EXPECTED_OUTPUT_DIR / "1273" / "1273 - يونس محمد ملاك"
    house_dir.mkdir(parents=True, exist_ok=True)
    source_files_dir = house_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    (source_files_dir / "1273_raw_append.pdf").touch()
    
    orchestrator = FSUIOrchestrator(mock_config, mock_llm)
    
    with patch.dict('sys.modules', {'fitz': MagicMock()}):
        mock_fitz = __import__('sys').modules['fitz']
        mock_doc = MagicMock()
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.page_count = 1
        
        def mock_save2(path, *args, **kwargs):
            Path(path).touch()
        mock_doc.save.side_effect = mock_save2
        
        mock_fitz.open.return_value = mock_doc
        
        with patch("src.pdf.compress.compress_pdf", create=True), \
             patch("src.pipeline.runner.run_generation_pass", create=True) as mock_generation:
             
            orchestrator.finalize(test_file)
            
            assert not tmp_dir.exists(), "The temporary directory should be removed after finalization"
            assert not test_file.exists(), "The OK file should be removed after finalization"
        
        # Generation pass might not be called if we wrote "[]" to routed_append_mode.json
        # But we verify it completes without errors
