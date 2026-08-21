import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.ingest.core import run_ingest_mode
from src.core.config import AppConfig

class DummyArgs:
    def __init__(self, input_path, dry_run=False):
        self.input_path = input_path
        self.dry_run = dry_run

def test_ingest_report_generated(tmp_path):
    # Setup directories
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    pdf_file = input_dir / "test1.pdf"
    pdf_file.touch()

    areas_root = tmp_path / "areas"
    areas_root.mkdir()

    config = AppConfig(areas_root_path=str(areas_root), provider="test", inbox_path=str(input_dir))

    # Mock the dependencies inside core.py
    with patch("src.ingest.core.process_unclassified_pdf") as mock_process, \
         patch("pypdf.PdfReader") as mock_pdf_reader:
        
        # Mock process_unclassified_pdf to create the raw dump
        def fake_process(*args, **kwargs):
            dump_data = {
                "groups": [
                    {
                        "expected_house_number": "711",
                        "expected_tenant_name": "John Doe",
                        "category": "Contracts",
                        "start_page": 0,
                        "end_page": 1
                    }
                ]
            }
            dump_path = input_dir / "test1.raw_dump.json"
            with open(dump_path, "w") as f:
                json.dump(dump_data, f)
                
        mock_process.side_effect = fake_process
        
        # Mock PDF pages
        mock_reader_inst = MagicMock()
        mock_reader_inst.pages = [1, 2] # 2 pages
        mock_pdf_reader.return_value = mock_reader_inst
        
        args = DummyArgs(input_path=str(input_dir), dry_run=False)
        llm_client = MagicMock()
        
        ret = run_ingest_mode(args, config, llm_client)
        assert ret == 0
        
        target_house_dir = areas_root / "711"
        assert target_house_dir.exists()
        
        source_files = target_house_dir / ".source_files"
        assert source_files.exists()
        
        report_path = source_files / "ingest_report.json"
        assert report_path.exists(), "ingest_report.json was not generated"
        
        with open(report_path, "r") as f:
            report_data = json.load(f)
            
        assert report_data["pdfs_processed"] == 1
        assert report_data["errors"] == 0
        assert report_data["pages_ingested"] == 2
