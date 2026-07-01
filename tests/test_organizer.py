import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.organizer import FileOrganizer
from src.schemas import DocumentGroup, Category, UserConfig, ConfigRouting, ConfigExtraction, ConfigCleaning, ConfigGrouping, ConfigCategory

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
            destination_format="{primary_tenant}/{category}",
            fallback_folder="UNKNOWN"
        )
    )

@patch('src.organizer.extract_pdf_segment')
def test_basic_structure(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(0, 1, "Resident A", Category.BASIC_DETAILS, ["2023-01-01"]),
        DocumentGroup(2, 3, "Resident B", Category.PERSONAL_DETAILS, ["2023-01-02"]),
        DocumentGroup(4, 5, "Resident A", Category.CONTRACT, ["NONE"]),
    ]
    summary = organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    
    # 2 residents
    res_a_dir = tmp_path / "Resident A"
    res_b_dir = tmp_path / "Resident B"
    assert res_a_dir.exists()
    assert res_b_dir.exists()
    
    # Dynamic folders: A has 2 (BASIC_DETAILS, CONTRACT), B has 1 (PERSONAL_DETAILS)
    assert len(list(res_a_dir.iterdir())) == 2
    assert len(list(res_b_dir.iterdir())) == 1
    
    assert len(summary) == 3

@patch('src.organizer.extract_pdf_segment')
def test_resident_ordering(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(0, 1, "Resident B", Category.BASIC_DETAILS, []),
        DocumentGroup(2, 3, "Resident A", Category.PERSONAL_DETAILS, []),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    
    assert (tmp_path / "Resident B").exists()
    assert (tmp_path / "Resident A").exists()


@patch('src.organizer.extract_pdf_segment')
def test_house_letters_routing(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(0, 1, "NONE", Category.OTHER_LETTERS, []),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    
    mock_extract.assert_any_call("123.pdf", 0, 1, str(tmp_path / "UNKNOWN" / "nodate_other_letters_unknown.pdf"))

@patch('src.organizer.extract_pdf_segment')
def test_continuation_pages_merged(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(5, 8, "Resident A", Category.BASIC_DETAILS, ["2023-01-05"]),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    target_path = tmp_path / "Resident A" / "BASIC_DETAILS" / "2023-01-05_basic_details_Resident A.pdf"
    mock_extract.assert_called_once_with("123.pdf", 5, 8, str(target_path))



@patch('src.organizer.extract_pdf_segment')
def test_counter_fallback_naming(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(0, 1, "Resident A", Category.NOTIFICATIONS, ["2023-01-01"]),
        DocumentGroup(2, 3, "Resident A", Category.NOTIFICATIONS, ["2023-01-01"]),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    target_path_1 = tmp_path / "Resident A" / "NOTIFICATIONS" / "2023-01-01_notifications_Resident A.pdf"
    target_path_2 = tmp_path / "Resident A" / "NOTIFICATIONS" / "2023-01-01_notifications_Resident A_2.pdf"
    mock_extract.assert_any_call("123.pdf", 0, 1, str(target_path_1))
    mock_extract.assert_any_call("123.pdf", 2, 3, str(target_path_2))

@patch('src.organizer.extract_pdf_segment')
def test_overwrite_behavior(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(0, 1, "Resident A", Category.BASIC_DETAILS, []),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    
    assert (tmp_path / "Resident A" / "BASIC_DETAILS").exists()
    
    # Organize again
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    assert (tmp_path / "Resident A" / "BASIC_DETAILS").exists()

@patch('src.organizer.extract_pdf_segment')
def test_unknown_tenant_filtered(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(0, 1, "UNKNOWN", Category.BASIC_DETAILS, []),
    ]
    organizer.organize(docs, "123.pdf", tmp_path, mock_config)
    assert not (tmp_path / "UNKNOWN_TENANT").exists()
    assert (tmp_path / "UNKNOWN").exists()

