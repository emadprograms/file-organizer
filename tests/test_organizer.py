import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.organizer import FileOrganizer
from src.schemas import DocumentGroup, Category

@pytest.fixture
def organizer():
    return FileOrganizer()

@patch('src.organizer.extract_pdf_segment')
def test_basic_structure(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "Resident A", Category.BASIC_DETAILS, []),
        DocumentGroup(2, 3, "Resident B", Category.PERSONAL_DETAILS, []),
        DocumentGroup(4, 5, "Resident A", Category.CONTRACT, []),
    ]
    summary = organizer.organize(docs, "123.pdf", tmp_path)
    
    house_dir = tmp_path / "123"
    assert house_dir.exists()
    
    # 2 residents
    res_a_dir = house_dir / "1_Resident A"
    res_b_dir = house_dir / "2_Resident B"
    assert res_a_dir.exists()
    assert res_b_dir.exists()
    
    # Dynamic folders: A has 2 (BASIC_DETAILS, CONTRACT), B has 1 (PERSONAL_DETAILS)
    assert len(list(res_a_dir.iterdir())) == 2
    assert len(list(res_b_dir.iterdir())) == 1
    
    assert len(summary) == 3

@patch('src.organizer.extract_pdf_segment')
def test_resident_ordering(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "Resident B", Category.BASIC_DETAILS, []),
        DocumentGroup(2, 3, "Resident A", Category.PERSONAL_DETAILS, []),
    ]
    organizer.organize(docs, "123.pdf", tmp_path)
    
    house_dir = tmp_path / "123"
    assert (house_dir / "1_Resident B").exists()
    assert (house_dir / "2_Resident A").exists()



@patch('src.organizer.extract_pdf_segment')
def test_house_letters_routing(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "NONE", Category.OTHER_LETTERS, []),
    ]
    organizer.organize(docs, "123.pdf", tmp_path)
    
    house_dir = tmp_path / "123"
    mock_extract.assert_any_call("123.pdf", 0, 1, str(house_dir / "رسائل عامة" / "other_letters_1.pdf"))

@patch('src.organizer.extract_pdf_segment')
def test_continuation_pages_merged(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(5, 8, "Resident A", Category.BASIC_DETAILS, []),
    ]
    organizer.organize(docs, "123.pdf", tmp_path)
    house_dir = tmp_path / "123"
    target_path = house_dir / "1_Resident A" / "01_البيانات الاساسية" / "basic_details_1.pdf"
    mock_extract.assert_called_once_with("123.pdf", 5, 8, str(target_path))



@patch('src.organizer.extract_pdf_segment')
def test_counter_fallback_naming(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "Resident A", Category.NOTIFICATIONS, []),
        DocumentGroup(2, 3, "Resident A", Category.NOTIFICATIONS, []),
    ]
    organizer.organize(docs, "123.pdf", tmp_path)
    house_dir = tmp_path / "123"
    target_path_1 = house_dir / "1_Resident A" / "09_الاشعارات" / "notifications_1.pdf"
    target_path_2 = house_dir / "1_Resident A" / "09_الاشعارات" / "notifications_2.pdf"
    mock_extract.assert_any_call("123.pdf", 0, 1, str(target_path_1))
    mock_extract.assert_any_call("123.pdf", 2, 3, str(target_path_2))

@patch('src.organizer.extract_pdf_segment')
def test_overwrite_behavior(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "Resident A", Category.BASIC_DETAILS, []),
    ]
    organizer.organize(docs, "123.pdf", tmp_path)
    
    # Create a dummy file in the output
    dummy_file = tmp_path / "123" / "dummy.txt"
    dummy_file.touch()
    assert dummy_file.exists()
    
    # Organize again
    organizer.organize(docs, "123.pdf", tmp_path)
    assert not dummy_file.exists()

@patch('src.organizer.extract_pdf_segment')
def test_unknown_tenant_filtered(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "UNKNOWN", Category.BASIC_DETAILS, []),
    ]
    organizer.organize(docs, "123.pdf", tmp_path)
    house_dir = tmp_path / "123"
    assert not (house_dir / "1_UNKNOWN").exists()
