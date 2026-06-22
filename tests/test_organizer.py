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
        DocumentGroup(0, 1, "123", "Resident A", Category.BASIC_DETAILS, []),
        DocumentGroup(2, 3, "123", "Resident B", Category.PERSONAL_DETAILS, []),
        DocumentGroup(4, 5, "123", "Resident A", Category.CONTRACT, []),
    ]
    summary = organizer.organize(docs, "dummy.pdf", tmp_path)
    
    house_dir = tmp_path / "123"
    assert house_dir.exists()
    
    # 2 residents
    res_a_dir = house_dir / "1_Resident_A"
    res_b_dir = house_dir / "2_Resident_B"
    assert res_a_dir.exists()
    assert res_b_dir.exists()
    
    # 13 subfolders in each
    assert len(list(res_a_dir.iterdir())) == 13
    assert len(list(res_b_dir.iterdir())) == 13
    
    # root level folders
    assert (house_dir / "amar_takhsees").exists()
    assert (house_dir / "house_letters").exists()
    
    assert len(summary) == 3

@patch('src.organizer.extract_pdf_segment')
def test_resident_ordering(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "123", "Resident B", Category.BASIC_DETAILS, []),
        DocumentGroup(2, 3, "123", "Resident A", Category.PERSONAL_DETAILS, []),
    ]
    organizer.organize(docs, "dummy.pdf", tmp_path)
    
    house_dir = tmp_path / "123"
    assert (house_dir / "1_Resident_B").exists()
    assert (house_dir / "2_Resident_A").exists()

@patch('src.organizer.extract_pdf_segment')
def test_amar_takhsees_routing(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "123", "Resident A", Category.AMAR_TAKHSEES, []),
        DocumentGroup(2, 3, "123", "Resident B", Category.BASIC_DETAILS, []),
    ]
    organizer.organize(docs, "dummy.pdf", tmp_path)
    
    # Resident A ONLY has amar takhsees, so should not have a resident folder
    house_dir = tmp_path / "123"
    assert not (house_dir / "1_Resident_A").exists()
    
    # Resident B is the first valid resident
    assert (house_dir / "1_Resident_B").exists()
    
    # AMAR_TAKHSEES should be in amar_takhsees folder
    mock_extract.assert_any_call("dummy.pdf", 0, 1, str(house_dir / "amar_takhsees" / "amar_takhsees_1.pdf"))

@patch('src.organizer.extract_pdf_segment')
def test_house_letters_routing(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "123", "UNKNOWN", Category.OTHER_LETTERS, []),
    ]
    organizer.organize(docs, "dummy.pdf", tmp_path)
    
    house_dir = tmp_path / "123"
    mock_extract.assert_any_call("dummy.pdf", 0, 1, str(house_dir / "house_letters" / "other_letters_1.pdf"))

@patch('src.organizer.extract_pdf_segment')
def test_continuation_pages_merged(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(5, 8, "123", "Resident A", Category.BASIC_DETAILS, []),
    ]
    organizer.organize(docs, "dummy.pdf", tmp_path)
    house_dir = tmp_path / "123"
    target_path = house_dir / "1_Resident_A" / "1_basic_details" / "basic_details_1.pdf"
    mock_extract.assert_called_once_with("dummy.pdf", 5, 8, str(target_path))

@patch('src.organizer.extract_pdf_segment')
def test_date_based_naming(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "123", "Resident A", Category.NOTIFICATIONS, ["2023-05-20"]),
    ]
    organizer.organize(docs, "dummy.pdf", tmp_path)
    house_dir = tmp_path / "123"
    target_path = house_dir / "1_Resident_A" / "9_notifications" / "2023-05-20_notifications.pdf"
    mock_extract.assert_called_once_with("dummy.pdf", 0, 1, str(target_path))

@patch('src.organizer.extract_pdf_segment')
def test_counter_fallback_naming(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "123", "Resident A", Category.NOTIFICATIONS, []),
        DocumentGroup(2, 3, "123", "Resident A", Category.NOTIFICATIONS, []),
    ]
    organizer.organize(docs, "dummy.pdf", tmp_path)
    house_dir = tmp_path / "123"
    target_path_1 = house_dir / "1_Resident_A" / "9_notifications" / "notifications_1.pdf"
    target_path_2 = house_dir / "1_Resident_A" / "9_notifications" / "notifications_2.pdf"
    mock_extract.assert_any_call("dummy.pdf", 0, 1, str(target_path_1))
    mock_extract.assert_any_call("dummy.pdf", 2, 3, str(target_path_2))

@patch('src.organizer.extract_pdf_segment')
def test_overwrite_behavior(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "123", "Resident A", Category.BASIC_DETAILS, []),
    ]
    organizer.organize(docs, "dummy.pdf", tmp_path)
    
    # Create a dummy file in the output
    dummy_file = tmp_path / "123" / "dummy.txt"
    dummy_file.touch()
    assert dummy_file.exists()
    
    # Organize again
    organizer.organize(docs, "dummy.pdf", tmp_path)
    assert not dummy_file.exists()

@patch('src.organizer.extract_pdf_segment')
def test_unknown_tenant_filtered(mock_extract, organizer, tmp_path):
    docs = [
        DocumentGroup(0, 1, "123", "UNKNOWN", Category.BASIC_DETAILS, []),
    ]
    organizer.organize(docs, "dummy.pdf", tmp_path)
    house_dir = tmp_path / "123"
    assert not (house_dir / "1_UNKNOWN").exists()
