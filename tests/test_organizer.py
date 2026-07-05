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


@patch('src.processing.organizer.Path.replace')
def test_reconciliation_manifest_generation(mock_replace, tmp_path):
    per_page = [
        {"page_index": 0, "tenant": "A", "date": "2020", "output_file": "file.pdf", "page_in_output": 1},
    ]
    summary = {"total_output_pages": 1, "output_file_count": 1}
    
    run_reconciliation(summary, per_page, 1, "HOUSE_123", tmp_path)
    
    manifest_file = tmp_path / "HOUSE_123_manifest.json"
    tmp_file = manifest_file.with_suffix('.tmp')
    
    # Verify atomicity
    mock_replace.assert_called_once_with(manifest_file)
    
    # Verify content written to the temp file
    assert tmp_file.exists()
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


@patch('src.processing.organizer.Path.replace')
def test_reconciliation_manifest_generation(mock_replace, tmp_path):
    per_page = [
        {"page_index": 0, "tenant": "A", "date": "2020", "output_file": "file.pdf", "page_in_output": 1},
    ]
    summary = {"total_output_pages": 1, "output_file_count": 1}
    
    run_reconciliation(summary, per_page, 1, "HOUSE_123", tmp_path)
    
    manifest_file = tmp_path / "HOUSE_123_manifest.json"
    tmp_file = manifest_file.with_suffix('.tmp')
    
    # Verify atomicity
    mock_replace.assert_called_once_with(manifest_file)
    
    # Verify content written to the temp file
    assert tmp_file.exists()
    with open(tmp_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["summary"]["house_id"] == "HOUSE_123"
        assert data["summary"]["total_input_pages"] == 1
        assert data["summary"]["total_output_pages"] == 1
        assert data["summary"]["output_file_count"] == 1
        assert data["summary"]["unaccounted_pages"] == []
        assert len(data["per_page"]) == 1
        assert data["per_page"][0]["tenant"] == "A"

@patch('src.processing.organizer.extract_pdf_segment')
def test_organize_empty_documents(mock_extract, organizer, mock_config, tmp_path):
    result = organizer.organize([], "123.pdf", "HOUSE_123", tmp_path, mock_config)
    assert result == []
    mock_extract.assert_not_called()

@patch('src.processing.organizer.os.makedirs')
@patch('src.processing.organizer.extract_pdf_segment')
def test_organize_dry_run(mock_extract, mock_makedirs, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="1_requests_and_applications", is_direct_routed=True),
    ]
    summary = organizer.organize(docs, "123.pdf", "HOUSE_123", tmp_path, mock_config, dry_run=True)
    mock_makedirs.assert_not_called()
    mock_extract.assert_not_called()
    assert len(summary) == 2

@patch('src.processing.organizer.extract_pdf_segment')
def test_organize_filename_conflict(mock_extract, organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=0, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="1_requests_and_applications", is_direct_routed=True),
        DocumentGroup(start_page=1, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="1_requests_and_applications", is_direct_routed=True),
    ]
    organizer.organize(docs, "123.pdf", "HOUSE_123", tmp_path, mock_config)
    
    calls = mock_extract.call_args_list
    assert len(calls) == 2
    assert calls[0][0][3].endswith("2023-01-01.pdf")
    assert calls[1][0][3].endswith("2023-01-01_2.pdf")

def test_organize_path_traversal(organizer, mock_config, tmp_path):
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="../../../../../../../../../malicious", is_direct_routed=True),
    ]
    with pytest.raises(ValueError, match="Path traversal detected"):
        organizer.organize(docs, "123.pdf", "HOUSE_123", tmp_path, mock_config)

@patch('src.processing.organizer.Path.replace')
def test_reconciliation_dry_run(mock_replace, tmp_path):
    per_page = [
        {"page_index": 0, "tenant": "A", "date": "2020", "output_file": "file.pdf", "page_in_output": 1},
    ]
    summary = {"total_output_pages": 1, "output_file_count": 1}
    
    run_reconciliation(summary, per_page, 1, "HOUSE_123", tmp_path, dry_run=True)
    
    mock_replace.assert_not_called()
    assert not (tmp_path / "HOUSE_123_manifest.json").exists()
