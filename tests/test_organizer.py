import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.processing.organizer import FileOrganizer
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
def test_basic_structure(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="1_requests_and_applications", is_direct_routed=True),
        DocumentGroup(start_page=2, end_page=3, primary_tenant="Resident B", category="PERSONAL_DETAILS", dates=["2023-01-02"], folder_path="2_personal_details", is_direct_routed=True),
        DocumentGroup(start_page=4, end_page=5, primary_tenant="Resident A", category="CONTRACT", dates=["NONE"], folder_path="5_contract", is_direct_routed=True),
    ]
    summary = organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    
    assert (tmp_path / "1_requests_and_applications" / "Resident A").exists()
    assert (tmp_path / "2_personal_details" / "Resident B").exists()
    assert (tmp_path / "5_contract" / "Resident A").exists()
    
    assert len(summary) == 3

@patch('src.processing.organizer.extract_pdf_segment')
def test_resident_ordering(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident B", category="BASIC_DETAILS", dates=[], folder_path="1_requests_and_applications"),
        DocumentGroup(start_page=2, end_page=3, primary_tenant="Resident A", category="PERSONAL_DETAILS", dates=[], folder_path="2_personal_details"),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    
    assert (tmp_path / "1_requests_and_applications" / "Resident B").exists()
    assert (tmp_path / "2_personal_details" / "Resident A").exists()


@patch('src.processing.organizer.extract_pdf_segment')
def test_house_letters_routing(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="NONE", category="OTHER_LETTERS", dates=[], folder_path="13_others", is_direct_routed=False, brief_arabic_title="رسالة"),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    
    mock_extract.assert_any_call("123.pdf", 0, 1, str(tmp_path / "13_others" / "unknown" / "nodate - رسالة.pdf"))

@patch('src.processing.organizer.extract_pdf_segment')
def test_continuation_pages_merged(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=5, end_page=8, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-05"], folder_path="1_requests_and_applications", is_direct_routed=True),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    target_path = tmp_path / "1_requests_and_applications" / "Resident A" / "2023-01-05.pdf"
    mock_extract.assert_called_once_with("123.pdf", 5, 8, str(target_path))


@patch('src.processing.organizer.extract_pdf_segment')
def test_counter_fallback_naming(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="NOTIFICATIONS", dates=["2023-01-01"], folder_path="12_tenant_correspondence", is_direct_routed=False, brief_arabic_title="تنبيه"),
        DocumentGroup(start_page=2, end_page=3, primary_tenant="Resident A", category="NOTIFICATIONS", dates=["2023-01-01"], folder_path="12_tenant_correspondence", is_direct_routed=False, brief_arabic_title="تنبيه"),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    target_path_1 = tmp_path / "12_tenant_correspondence" / "Resident A" / "2023-01-01 - تنبيه.pdf"
    target_path_2 = tmp_path / "12_tenant_correspondence" / "Resident A" / "2023-01-01 - تنبيه_2.pdf"
    mock_extract.assert_any_call("123.pdf", 0, 1, str(target_path_1))
    mock_extract.assert_any_call("123.pdf", 2, 3, str(target_path_2))

@patch('src.processing.organizer.extract_pdf_segment')
def test_overwrite_behavior(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=[], folder_path="1_requests_and_applications"),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    
    assert (tmp_path / "1_requests_and_applications" / "Resident A").exists()
    
    # Organize again
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    assert (tmp_path / "1_requests_and_applications" / "Resident A").exists()

@patch('src.processing.organizer.extract_pdf_segment')
def test_unknown_tenant_filtered(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="UNKNOWN", category="BASIC_DETAILS", dates=[], folder_path="1_requests_and_applications"),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    assert not (tmp_path / "1_requests_and_applications" / "UNKNOWN_TENANT").exists()
    assert (tmp_path / "1_requests_and_applications" / "unknown").exists()
