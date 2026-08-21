import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from src.ingest.core import run_ingest_mode
from src.core.config import AppConfig

class DummyArgs:
    def __init__(self, input_path, dry_run=False, model=None):
        self.input_path = input_path
        self.dry_run = dry_run
        self.model = model

@patch('src.ingest.core.process_unclassified_pdf')
def test_ingest_preserves_raw_dump(mock_process, tmp_path):
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    input_dir = tmp_path / "inbox"
    input_dir.mkdir()
    
    pdf_path = input_dir / "514.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(pdf_path, "wb") as f:
        writer.write(f)
        
    raw_dump_path = input_dir / "514.raw_dump.json"
    with open(raw_dump_path, "w", encoding="utf-8") as f:
        json.dump([{"expected_house_number": "514", "expected_tenant_name": "Test Tenant", "category": "others"}], f)
        
    config = AppConfig(inbox_path=str(input_dir), areas_root_path=str(areas_root))
    config.areas_root_path = str(areas_root)
    args = DummyArgs(input_path=str(input_dir))
    
    res = run_ingest_mode(args, config, None)
    assert res == 0
    
    # Assert raw_dump was preserved in .source_files
    source_files = areas_root / "514" / ".source_files"
    assert (source_files / "514.raw_dump.json").exists()

@patch('src.ingest.core.process_unclassified_pdf')
def test_ingest_page_count_validation(mock_process, tmp_path):
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    input_dir = tmp_path / "inbox"
    input_dir.mkdir()
    
    pdf_path = input_dir / "514.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100)
    with open(pdf_path, "wb") as f:
        writer.write(f)
        
    # Dump has only 1 page, PDF has 2
    raw_dump_path = input_dir / "514.raw_dump.json"
    with open(raw_dump_path, "w", encoding="utf-8") as f:
        json.dump([{"expected_house_number": "514", "expected_tenant_name": "Test Tenant", "category": "others"}], f)
        
    config = AppConfig(inbox_path=str(input_dir), areas_root_path=str(areas_root))
    config.areas_root_path = str(areas_root)
    args = DummyArgs(input_path=str(input_dir))
    
    with pytest.raises(ValueError):
        run_ingest_mode(args, config, None)

@patch('src.ingest.core.process_unclassified_pdf')
def test_ingest_writes_yaml_data(mock_process, tmp_path):
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    input_dir = tmp_path / "inbox"
    input_dir.mkdir()
    
    pdf_path = input_dir / "514.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(pdf_path, "wb") as f:
        writer.write(f)
        
    raw_dump_path = input_dir / "514.raw_dump.json"
    with open(raw_dump_path, "w", encoding="utf-8") as f:
        json.dump({"groups": [{"start_page": 0, "end_page": 0, "expected_house_number": "514", "expected_tenant_name": "Real Tenant", "category": "others"}]}, f)
        
    config = AppConfig(inbox_path=str(input_dir), areas_root_path=str(areas_root))
    config.areas_root_path = str(areas_root)
    args = DummyArgs(input_path=str(input_dir))
    
    res = run_ingest_mode(args, config, None)
    assert res == 0
    
    source_files = areas_root / "514" / ".source_files"
    yaml_path = source_files / "514_1_tenants.yaml"
    assert yaml_path.exists()
    
    content = yaml_path.read_text(encoding="utf-8")
    assert "Real Tenant" in content
    assert "Unassigned" not in content
