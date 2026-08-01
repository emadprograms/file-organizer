from typing import Any
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.timeline import FileOrganizer, run_reconciliation
from src.core.schemas import DocumentGroup

@pytest.fixture
def organizer() -> Any:
    """
    Provide the organizer fixture/mock.

    Returns:
    The appropriate fixture or mock value.
    """
    return FileOrganizer()

@pytest.fixture
def mock_config() -> None:
    """
    Provide the mock config fixture/mock.

    Returns:
    The appropriate fixture or mock value.
    """
    return None

@patch('src.timeline.core.extract_pdf_segment')
def test_create_house_directory(mock_extract, organizer, mock_config, tmp_path) -> None:
    """
    Test create house directory.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "123.pdf").touch()
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="بيانات أساسية", is_direct_routed=True),
    ]
    summary = organizer.organize(docs, str(input_dir / "123.pdf"), "HOUSE_123", tmp_path, mock_config)
    assert (tmp_path / "HOUSE_123 - Resident A").exists()
    assert (tmp_path / "HOUSE_123 - Resident A" / "Resident A \u200E(2023 - 2023)\u200E").exists()

@patch('src.timeline.core.extract_pdf_segment')
def test_tenant_directories_timeline(mock_extract, organizer, mock_config, tmp_path) -> None:
    """
    Test tenant directories timeline.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir(exist_ok=True)
    (input_dir / "123.pdf").touch(exist_ok=True)
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2020-01-01"], folder_path="بيانات أساسية", is_direct_routed=True),
        DocumentGroup(start_page=2, end_page=3, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="بيانات أساسية", is_direct_routed=True),
    ]
    summary = organizer.organize(docs, str(input_dir / "123.pdf"), "HOUSE_123", tmp_path, mock_config)
    assert (tmp_path / "HOUSE_123 - Resident A" / "Resident A \u200E(2020 - 2023)\u200E").exists()

@patch('src.timeline.core.extract_pdf_segment')
def test_on_demand_topic_creation(mock_extract, organizer, mock_config, tmp_path) -> None:
    """
    Test on demand topic creation.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir(exist_ok=True)
    (input_dir / "123.pdf").touch(exist_ok=True)
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2020-01-01"], folder_path="بيانات أساسية", is_direct_routed=True),
    ]
    organizer.organize(docs, str(input_dir / "123.pdf"), "HOUSE_123", tmp_path, mock_config)
    assert (tmp_path / "HOUSE_123 - Resident A" / "Resident A \u200E(2020 - 2020)\u200E" / "01_بيانات أساسية").exists()
    assert (tmp_path / "HOUSE_123 - Resident A" / "Resident A \u200E(2020 - 2020)\u200E" / "02_بيانات شخصية").exists()

@patch('src.timeline.core.extract_pdf_segment')
def test_hardcoded_routing(mock_extract, organizer, mock_config, tmp_path) -> None:
    """
    Test hardcoded routing.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir(exist_ok=True)
    (input_dir / "123.pdf").touch(exist_ok=True)
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="OTHER_LETTERS", dates=[], folder_path="رسائل متنوعة", is_direct_routed=False, brief_arabic_title="رسالة"),
    ]
    organizer.organize(docs, str(input_dir / "123.pdf"), "HOUSE_123", tmp_path, mock_config)
    assert mock_extract.called
    args, kwargs = mock_extract.call_args
    assert "vault" in args[3]
    assert ".tmp.pdf" in args[3]
    assert (tmp_path / "HOUSE_123" / "Resident A" / "13_رسائل متنوعة" / "nodate - رسالة.lnk").exists()

@patch('src.timeline.core.extract_pdf_segment')
def test_unassigned_folder_period(mock_extract, organizer, mock_config, tmp_path) -> None:
    """
    Test unassigned folder period.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir(exist_ok=True)
    (input_dir / "123.pdf").touch(exist_ok=True)
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Unassigned (2020-05)", category="BASIC_DETAILS", dates=["2020-01-01", "2021-01-01"], folder_path="بيانات أساسية", is_direct_routed=True),
        DocumentGroup(start_page=2, end_page=3, primary_tenant="Unassigned (2021-05)", category="BASIC_DETAILS", dates=["2023-01-01", "2023-01-01"], folder_path="بيانات أساسية", is_direct_routed=True),
    ]
    organizer.organize(docs, str(input_dir / "123.pdf"), "HOUSE_123", tmp_path, mock_config)
    assert (tmp_path / "HOUSE_123" / "غير مخصص (فترة مستنتجة) \u200E(2020-01 - 2023-01)\u200E").exists()

@patch('src.timeline.core.extract_pdf_segment')
def test_unassigned_folder_fallback(mock_extract, organizer, mock_config, tmp_path) -> None:
    """
    Test unassigned folder fallback.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir(exist_ok=True)
    (input_dir / "123.pdf").touch(exist_ok=True)
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Unassigned", category="BASIC_DETAILS", dates=["NONE", "NONE"], folder_path="بيانات أساسية", is_direct_routed=True),
    ]
    organizer.organize(docs, str(input_dir / "123.pdf"), "HOUSE_123", tmp_path, mock_config)
    assert (tmp_path / "HOUSE_123" / "غير مخصص").exists()

def test_page_count_reconciliation(tmp_path) -> None:
    """
    Test page count reconciliation.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
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

def test_reconciliation_manifest(tmp_path) -> None:
    """
    Test reconciliation manifest.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    per_page = [
        {"page_index": 0, "tenant": "A", "date": "2020", "output_file": "file.pdf", "page_in_output": 1},
    ]
    summary = {"total_output_pages": 1, "output_file_count": 1}
    run_reconciliation(summary, per_page, 1, "HOUSE_123", tmp_path)
    
    manifest_file = tmp_path / ".source_files" / "HOUSE_123_state.json"
    assert manifest_file.exists()
    
    with open(manifest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert data["manifest"]["summary"]["output_file_count"] == 1


@patch('src.utils.fs.shutil.move')
def test_reconciliation_manifest_generation(mock_replace, tmp_path) -> None:
    """
    Test reconciliation manifest generation.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    per_page = [
        {"page_index": 0, "tenant": "A", "date": "2020", "output_file": "file.pdf", "page_in_output": 1},
    ]
    summary = {"total_output_pages": 1, "output_file_count": 1}
    
    run_reconciliation(summary, per_page, 1, "HOUSE_123", tmp_path)
    
    manifest_file = tmp_path / "HOUSE_123_manifest.json"
    
    # Verify atomicity
    mock_replace.assert_called_once()
    
    # Verify content written to the temp file
    tmp_file = Path(mock_replace.call_args[0][0])
    assert tmp_file.exists()
    with open(tmp_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["manifest"]["summary"]["house_id"] == "HOUSE_123"
        assert data["manifest"]["summary"]["total_input_pages"] == 1
        assert data["manifest"]["summary"]["total_output_pages"] == 1
        assert data["manifest"]["summary"]["output_file_count"] == 1
        assert data["manifest"]["summary"]["unaccounted_pages"] == []
        assert len(data["manifest"]["per_page"]) == 1
        assert data["manifest"]["per_page"][0]["tenant"] == "A"

@patch('src.utils.fs.shutil.move')
def test_reconciliation_manifest_merging(mock_replace, tmp_path) -> None:
    """Test that run_reconciliation correctly merges with an existing manifest."""
    source_files_dir = tmp_path / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = source_files_dir / "HOUSE_123_state.json"
    
    # Create an initial manifest representing previous runs
    initial_manifest = {
        "manifest": {
            "summary": {
                "house_id": "HOUSE_123",
                "total_input_pages": 5,
                "total_output_pages": 5,
                "output_file_count": 2,
                "unaccounted_pages": []
            },
            "per_page": [
                {"page_index": i, "tenant": "A", "date": "2020", "output_file": f"file_{i}.pdf", "page_in_output": 1}
                for i in range(5)
            ]
        }
    }
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(initial_manifest, f)
        
    # Mock data for append mode (e.g. 1 newly appended page)
    new_per_page = [
        {"page_index": 0, "tenant": "B", "date": "2021", "output_file": "new_file.pdf", "page_in_output": 1}
    ]
    new_summary = {"total_output_pages": 1, "output_file_count": 1}
    
    run_reconciliation(new_summary, new_per_page, 1, "HOUSE_123", tmp_path)
    
    # Verify atomicity logic used tmp_path and moved it. We need to check what was written to the tmp_path.
    mock_replace.assert_called_once()
    tmp_file = Path(mock_replace.call_args[0][0])
    
    with open(tmp_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["manifest"]["summary"]["total_input_pages"] == 6 # 5 + 1
        assert data["manifest"]["summary"]["total_output_pages"] == 6 # 5 + 1
        assert data["manifest"]["summary"]["output_file_count"] == 3 # 2 + 1
        assert len(data["manifest"]["per_page"]) == 6
        # Check that the new page had its page_index shifted by existing total_input_pages (5)
        assert data["manifest"]["per_page"][-1]["page_index"] == 5
        assert data["manifest"]["per_page"][-1]["tenant"] == "B"

@patch('src.timeline.core.extract_pdf_segment')
def test_organize_empty_documents(mock_extract, organizer, mock_config, tmp_path) -> None:
    """
    Test organize empty documents.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir(exist_ok=True)
    (input_dir / "123.pdf").touch(exist_ok=True)
    result = organizer.organize([], str(input_dir / "123.pdf"), "HOUSE_123", tmp_path, mock_config)
    assert result == ([], "HOUSE_123")
    mock_extract.assert_not_called()

@patch('src.timeline.core.os.makedirs')
@patch('src.timeline.core.extract_pdf_segment')
def test_organize_dry_run(mock_extract, mock_makedirs, organizer, mock_config, tmp_path) -> None:
    """
    Test organize dry run.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir(exist_ok=True)
    (input_dir / "123.pdf").touch(exist_ok=True)
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="بيانات أساسية", is_direct_routed=True),
    ]
    summary = organizer.organize(docs, str(input_dir / "123.pdf"), "HOUSE_123", tmp_path, mock_config, dry_run=True)
    mock_makedirs.assert_not_called()
    mock_extract.assert_not_called()
    assert len(summary) == 2

@patch('src.timeline.core.extract_pdf_segment')
def test_organize_filename_conflict(mock_extract, organizer, mock_config, tmp_path) -> None:
    """
    Test organize filename conflict.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir(exist_ok=True)
    (input_dir / "123.pdf").touch(exist_ok=True)
    docs = [
        DocumentGroup(start_page=0, end_page=0, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="بيانات أساسية", is_direct_routed=True),
        DocumentGroup(start_page=1, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="بيانات أساسية", is_direct_routed=True),
    ]
    organizer.organize(docs, str(input_dir / "123.pdf"), "HOUSE_123", tmp_path, mock_config)
    
    calls = mock_extract.call_args_list
    assert len(calls) == 2
    assert calls[0][0][3] != calls[1][0][3]
    assert "vault" in calls[0][0][3]
    assert (tmp_path / "HOUSE_123 - Resident A" / "Resident A \u200E(2023 - 2023)\u200E" / "01_بيانات أساسية" / "2023-01-01.lnk").exists()
    assert (tmp_path / "HOUSE_123 - Resident A" / "Resident A \u200E(2023 - 2023)\u200E" / "01_بيانات أساسية" / "2023-01-01_2.lnk").exists()

def test_organize_path_traversal(organizer, mock_config, tmp_path) -> None:
    """
    Test organize path traversal.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir(exist_ok=True)
    (input_dir / "123.pdf").touch(exist_ok=True)
    docs = [
        DocumentGroup(start_page=0, end_page=1, primary_tenant="Resident A", category="BASIC_DETAILS", dates=["2023-01-01"], folder_path="../../../../../../../../../malicious", is_direct_routed=True),
    ]
    with pytest.raises(ValueError, match="Path traversal detected"):
        organizer.organize(docs, str(input_dir / "123.pdf"), "HOUSE_123", tmp_path, mock_config)

@patch('src.timeline.page_integrity.Path.replace')
def test_reconciliation_dry_run(mock_replace, tmp_path) -> None:
    """
    Test reconciliation dry run.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    per_page = [
        {"page_index": 0, "tenant": "A", "date": "2020", "output_file": "file.pdf", "page_in_output": 1},
    ]
    summary = {"total_output_pages": 1, "output_file_count": 1}
    
    run_reconciliation(summary, per_page, 1, "HOUSE_123", tmp_path, dry_run=True)
    
    mock_replace.assert_not_called()
    assert not (tmp_path / "HOUSE_123_manifest.json").exists()

@patch('src.utils.fs.shutil.move')
def test_reconciliation_manifest_prepending(mock_replace, tmp_path) -> None:
    """Test that run_reconciliation correctly prepends with an existing manifest."""
    source_files_dir = tmp_path / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = source_files_dir / "HOUSE_123_state.json"
    
    initial_manifest = {
        "manifest": {
            "summary": {
                "house_id": "HOUSE_123",
                "total_input_pages": 5,
                "total_output_pages": 5,
                "output_file_count": 2,
                "unaccounted_pages": []
            },
            "per_page": [
                {"page_index": i, "tenant": "A", "date": "2020", "output_file": f"file_{i}.pdf", "page_in_output": 1}
                for i in range(5)
            ]
        }
    }
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(initial_manifest, f)
        
    new_per_page = [
        {"page_index": 0, "tenant": "B", "date": "2021", "output_file": "new_file.pdf", "page_in_output": 1}
    ]
    new_summary = {"total_output_pages": 1, "output_file_count": 1}
    
    run_reconciliation(new_summary, new_per_page, 1, "HOUSE_123", tmp_path, prepend=True)
    
    mock_replace.assert_called_once()
    tmp_file = Path(mock_replace.call_args[0][0])
    
    with open(tmp_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["manifest"]["summary"]["total_input_pages"] == 6
        assert data["manifest"]["summary"]["total_output_pages"] == 6
        assert data["manifest"]["summary"]["output_file_count"] == 3
        assert len(data["manifest"]["per_page"]) == 6
        
        assert data["manifest"]["per_page"][0]["page_index"] == 0
        assert data["manifest"]["per_page"][0]["tenant"] == "B"
        
        assert data["manifest"]["per_page"][1]["page_index"] == 1
        assert data["manifest"]["per_page"][1]["tenant"] == "A"

