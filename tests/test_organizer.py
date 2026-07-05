import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.processing.organizer import FileOrganizer, run_reconciliation
from src.core.schemas import DocumentGroup, UserConfig, ConfigRouting, ConfigExtraction, ConfigCleaning, ConfigGrouping, ConfigCategory

@pytest.fixture
def organizer():
    return FileOrganizer()

@pytest.fixture
def mock_config():
    return UserConfig(
        categories=[ConfigCategory(id="BASIC_DETAILS", name="Basic Details Form"), ConfigCategory(id="PERSONAL_DETAILS", name="Personal Identification"), ConfigCategory(id="CONTRACT", name="Housing Contract"), ConfigCategory(id="OTHER_LETTERS", name="Miscellaneous Letters"), ConfigCategory(id="NOTIFICATIONS", name="General Notifications")],
        extraction=ConfigExtraction(prompt_template="", fields=[]),
        cleaning=ConfigCleaning(strategy="python"),
        grouping=ConfigGrouping(strategy="declarative"),
        routing=ConfigRouting(
            strategy="template",
            rules={"BASIC_DETAILS": "BASIC_DETAILS", "PERSONAL_DETAILS": "PERSONAL_DETAILS", "CONTRACT": "CONTRACT", "OTHER_LETTERS": "OTHER_LETTERS", "NOTIFICATIONS": "NOTIFICATIONS"},
            fallback_folder="UNKNOWN"
        )
    )

@patch('src.processing.organizer.extract_pdf_segment')
def test_create_house_directory(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="1_requests_and_applications", is_direct_routed=True),
    ]
    summary = organizer.organize(docs, "123.pdf", "HOUSE_123", tmp_path, mock_config)
    assert (tmp_path / "HOUSE_123").exists()
    assert (tmp_path / "HOUSE_123" / "Resident A 2023-2023").exists()

@patch('src.processing.organizer.extract_pdf_segment')
def test_tenant_directories_timeline(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2020-01-01"], folder_path="1_requests_and_applications", is_direct_routed=True),
        DocumentGroup(start_page=2, end_page=3, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="1_requests_and_applications", is_direct_routed=True),
    ]
    summary = organizer.organize(docs, "123.pdf", "HOUSE_123", tmp_path, mock_config)
    assert (tmp_path / "HOUSE_123" / "Resident A 2020-2023").exists()

@patch('src.processing.organizer.extract_pdf_segment')
def test_on_demand_topic_creation(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2020-01-01"], folder_path="1_requests_and_applications", is_direct_routed=True),
    ]
    organizer.organize(docs, "123.pdf", "HOUSE_123", tmp_path, mock_config)
    assert (tmp_path / "HOUSE_123" / "Resident A 2020-2020" / "1_requests_and_applications").exists()
    assert not (tmp_path / "HOUSE_123" / "Resident A 2020-2020" / "2_personal_details").exists()

@patch('src.processing.organizer.extract_pdf_segment')
def test_hardcoded_routing(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="OTHER_LETTERS", dates=[], folder_path="13_others", is_direct_routed=False, brief_arabic_title="رسالة"),
    ]
    organizer.organize(docs, "123.pdf", "HOUSE_123", tmp_path, mock_config)
    mock_extract.assert_any_call("123.pdf", 0, 1, str(tmp_path / "HOUSE_123" / "Resident A" / "13_others" / "nodate - رسالة.pdf"))

@patch('src.processing.organizer.extract_pdf_segment')
def test_unassigned_folder_period(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Unassigned (2020-05)", category="BASIC_DETAILS", dates=["2020-01-01", "2021-01-01"], folder_path="1_requests_and_applications", is_direct_routed=True),
        DocumentGroup(start_page=2, end_page=3, primary_tenant="Unassigned (2021-05)", category="BASIC_DETAILS", dates=["2023-01-01", "2023-01-01"], folder_path="1_requests_and_applications", is_direct_routed=True),
    ]
    organizer.organize(docs, "123.pdf", "HOUSE_123", tmp_path, mock_config)
    assert (tmp_path / "HOUSE_123" / "غير محدد 2020-2023").exists()

@patch('src.processing.organizer.extract_pdf_segment')
def test_unassigned_folder_fallback(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Unassigned", category="BASIC_DETAILS", dates=["NONE", "NONE"], folder_path="1_requests_and_applications", is_direct_routed=True),
    ]
    organizer.organize(docs, "123.pdf", "HOUSE_123", tmp_path, mock_config)
    assert (tmp_path / "HOUSE_123" / "غير محدد").exists()

def test_page_count_reconciliation(tmp_path):
    per_page = [
        {"page_index": 0, "tenant": "A", "date": "2020", "output_file": "file.pdf", "page_in_output": 1},
        {"page_index": 1, "tenant": "A", "date": "2020", "output_file": "file.pdf", "page_in_output": 2},
    ]
    summary = {"total_output_pages": 2, "output_file_count": 1}
    # Should pass
    run_reconciliation(summary, per_page, 2, "HOUSE_123", tmp_path)
    
    # Should fail
    with pytest.raises(RuntimeError):
        run_reconciliation(summary, per_page, 3, "HOUSE_123", tmp_path)

def test_reconciliation_manifest(tmp_path):
    per_page = [
        {"page_index": 0, "tenant": "A", "date": "2020", "output_file": "file.pdf", "page_in_output": 1},
    ]
    summary = {"total_output_pages": 1, "output_file_count": 1}
    run_reconciliation(summary, per_page, 1, "HOUSE_123", tmp_path)
    
    manifest_file = tmp_path / "HOUSE_123_manifest.json"
    assert manifest_file.exists()
    
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        

