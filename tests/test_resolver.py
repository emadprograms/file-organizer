import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.inbox.resolver import (
    infer_missing_data,
    resolve_area,
    resolve_tenant,
    resolve_group_mode,
    ConflictError
)
from src.core.schemas import ParsedCommand

@patch("src.inbox.resolver.process_unclassified_pdf")
@patch("builtins.open")
@patch("pathlib.Path.exists")
def test_infer_missing_data(mock_exists, mock_open, mock_process):
    # Setup
    pdf_path = Path("/mock/inbox/test.pdf")
    parsed_cmd = ParsedCommand(area="A", house="U", tenant_hint="U", group="U", date="U", title="test")
    mock_exists.return_value = True
    
    # Mocking report content with a majority vote scenario
    import json
    mock_json = [
        {"expected_house_number": "123", "date": "2023"},
        {"expected_house_number": "123", "date": "2024"},
        {"expected_house_number": "456", "date": "2023"}
    ]
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_json)
    
    result = infer_missing_data(pdf_path, parsed_cmd, None)
    
    # Assertions
    mock_process.assert_called_once()
    assert result["expected_house_number"] == "123"
    assert result["date"] == "2023"


def test_resolve_area_conflict(tmp_path):
    # Setup directories
    areas_root = tmp_path / "areas"
    area1 = areas_root / "Area1"
    area2 = areas_root / "Area2"
    area1.mkdir(parents=True)
    area2.mkdir(parents=True)
    
    (area1 / "123").mkdir()
    (area2 / "123").mkdir()
    
    with pytest.raises(ConflictError):
        resolve_area("123", areas_root)


def test_resolve_area_success(tmp_path):
    areas_root = tmp_path / "areas"
    area1 = areas_root / "Area1"
    area1.mkdir(parents=True)
    (area1 / "123").mkdir()
    
    result = resolve_area("123", areas_root)
    assert result == "Area1"


def test_resolve_area_not_found(tmp_path):
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    
    with pytest.raises(ValueError):
        resolve_area("123", areas_root)


@patch("src.inbox.resolver.load_tenant_config")
@patch("src.inbox.resolver.canonicalize_with_llm")
def test_resolve_tenant(mock_canonicalize, mock_load):
    target_dir = Path("/mock/areas/Area1/123")
    
    # Hint is 'U' -> returns 'U'
    assert resolve_tenant(target_dir, "U", None) == "U"
    
    # Hint is not 'U', valid configs
    mock_load.return_value = [{"name": "Ali Abbas"}, {"name": "Hassan"}]
    mock_canonicalize.return_value = {"Ali": "Ali Abbas"}
    
    assert resolve_tenant(target_dir, "Ali", None) == "Ali Abbas"
    
    # Hint is not 'U' but not found in mappings (assuming canonicalize_with_llm handles it, but if it returns None)
    mock_canonicalize.return_value = {}
    assert resolve_tenant(target_dir, "Unknown", None) == "U"


def test_resolve_group_mode():
    assert resolve_group_mode("G") == {"skip_grouping": True, "skip_routing": False}
    assert resolve_group_mode("U") == {"skip_grouping": False, "skip_routing": False}
    
    # Valid group number '5' maps to '05' prefix, which is 'عقود' in FOLDER_PREFIXES
    res = resolve_group_mode("5")
    assert res["skip_grouping"] == True
    assert res["skip_routing"] == True
    assert res["folder_name"] == "05_عقود"
    
    # Invalid group number -> fallback
    assert resolve_group_mode("99") == {"skip_grouping": False, "skip_routing": False}
