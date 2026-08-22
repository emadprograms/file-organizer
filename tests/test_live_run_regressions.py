"""
Regression tests for ingest mode behavior.
Tests mock all LLM pipeline stages and exercise only the ingest
orchestration logic: state.json building, raw_dump preservation, YAML writing.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.ingest.core import run_ingest_mode
from src.core.config import AppConfig
from src.core.models import PageData
from src.core.schemas import DocumentGroup


class DummyArgs:
    def __init__(self, input_path, dry_run=False, model=None):
        self.input_path = input_path
        self.dry_run = dry_run
        self.model = model


def _make_pages(dump_list):
    return [
        PageData(
            category=item.get("category", "others"),
            content_explanation=item.get("content_explanation", ""),
            expected_tenant_name=item.get("expected_tenant_name"),
            original_index=i,
        )
        for i, item in enumerate(dump_list)
    ]


def _make_groups(pages):
    if not pages:
        return []
    return [
        DocumentGroup(
            start_page=0,
            end_page=len(pages) - 1,
            primary_tenant=pages[0].expected_tenant_name or "Unknown",
            category=pages[0].category or "others",
            dates=[],
            brief_arabic_title="Test",
            vault_id=None,
            user_locked=False,
            shortcuts=[],
        )
    ]


@patch('src.timeline.FileOrganizer.organize', return_value=([], "514"))
@patch('src.pipeline.runner.run_routing_pass', side_effect=lambda d, *a, **kw: d)
@patch('src.pipeline.runner.run_grouping_pass', side_effect=lambda p, *a, **kw: _make_groups(p))
@patch('src.pipeline.runner.run_fine_categorization_pass', side_effect=lambda p, *a, **kw: p)
@patch('src.pipeline.runner.run_cleaning_pass')
@patch('src.ingest.core.process_unclassified_pdf')
def test_ingest_preserves_raw_dump(
    mock_process, mock_clean, mock_fine, mock_group, mock_route, mock_organize, tmp_path
):
    """ingest must move raw_dump.json into .source_files after processing."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    input_dir = tmp_path / "inbox"
    input_dir.mkdir()

    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(input_dir / "514.pdf", "wb") as f:
        writer.write(f)

    dump = [{"expected_house_number": "514", "expected_tenant_name": "Test Tenant", "category": "others"}]
    raw_dump_path = input_dir / "514.raw_dump.json"
    with open(raw_dump_path, "w", encoding="utf-8") as f:
        json.dump(dump, f)

    pages = _make_pages(dump)
    mock_clean.return_value = (pages, None)

    config = AppConfig(inbox_path=str(input_dir), areas_root_path=str(areas_root))
    args = DummyArgs(input_path=str(input_dir))

    res = run_ingest_mode(args, config, MagicMock())
    assert res == 0

    # The raw_dump is moved into the state_dir: initially inbox/.source_files
    # (before organize rename), verify it moved out of inbox root
    assert not raw_dump_path.exists(), "raw_dump.json should have been moved from inbox"
    # After organize returns "514", ingest creates that subdir in the same parent dir (inbox)
    dest_dump = input_dir / "514" / ".source_files" / "514.raw_dump.json"
    assert dest_dump.exists(), f"raw_dump.json should be in .source_files, checked {dest_dump}"


@patch('src.pipeline.runner.run_cleaning_pass')
@patch('src.ingest.core.process_unclassified_pdf')
def test_ingest_page_count_validation(mock_process, mock_clean, tmp_path):
    """ingest processes successfully even when PDF page count != dump count.
    Page count enforcement is reconcile's responsibility, not ingest's."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    input_dir = tmp_path / "inbox"
    input_dir.mkdir()

    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100)  # 2 pages in PDF
    with open(input_dir / "514.pdf", "wb") as f:
        writer.write(f)

    # Dump has 1 item but PDF has 2 pages — ingest doesn't validate this
    dump = [{"expected_house_number": "514", "expected_tenant_name": "Test Tenant", "category": "others"}]
    with open(input_dir / "514.raw_dump.json", "w", encoding="utf-8") as f:
        json.dump(dump, f)

    pages = _make_pages(dump)
    mock_clean.return_value = (pages, None)

    config = AppConfig(inbox_path=str(input_dir), areas_root_path=str(areas_root))
    args = DummyArgs(input_path=str(input_dir))

    # ingest should NOT raise — it just records pdf_pages in the report
    with patch('src.timeline.FileOrganizer.organize', return_value=([], "514")), \
         patch('src.pipeline.runner.run_fine_categorization_pass', side_effect=lambda p, *a, **kw: p), \
         patch('src.pipeline.runner.run_grouping_pass', side_effect=lambda p, *a, **kw: []), \
         patch('src.pipeline.runner.run_routing_pass', side_effect=lambda d, *a, **kw: d):
        res = run_ingest_mode(args, config, MagicMock())
    assert res == 0


@patch('src.timeline.FileOrganizer.organize', return_value=([], "514"))
@patch('src.pipeline.runner.run_routing_pass', side_effect=lambda d, *a, **kw: d)
@patch('src.pipeline.runner.run_grouping_pass', side_effect=lambda p, *a, **kw: _make_groups(p))
@patch('src.pipeline.runner.run_fine_categorization_pass', side_effect=lambda p, *a, **kw: p)
@patch('src.pipeline.runner.run_cleaning_pass')
@patch('src.ingest.core.process_unclassified_pdf')
def test_ingest_writes_yaml_data(
    mock_process, mock_clean, mock_fine, mock_group, mock_route, mock_organize, tmp_path
):
    """ingest must write a _tenants.yaml with real tenant names (not Unassigned)."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    input_dir = tmp_path / "inbox"
    input_dir.mkdir()

    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(input_dir / "514.pdf", "wb") as f:
        writer.write(f)

    dump = [{"expected_house_number": "514", "expected_tenant_name": "Real Tenant", "category": "others"}]
    with open(input_dir / "514.raw_dump.json", "w", encoding="utf-8") as f:
        json.dump(dump, f)

    pages = _make_pages(dump)
    # Return yaml_data so the YAML file is written
    mock_clean.return_value = (pages, [{"name": "Real Tenant", "start_date": "2000-01-01", "end_date": "present"}])

    config = AppConfig(inbox_path=str(input_dir), areas_root_path=str(areas_root))
    args = DummyArgs(input_path=str(input_dir))

    res = run_ingest_mode(args, config, MagicMock())
    assert res == 0

    # YAML is written into .source_files adjacent to the original PDF location (inbox/.source_files)
    source_files = input_dir / ".source_files"
    yaml_path = source_files / "514_1_tenants.yaml"
    assert yaml_path.exists(), f"Expected YAML at {yaml_path}"

    content = yaml_path.read_text(encoding="utf-8")
    assert "Real Tenant" in content
    assert "Unassigned" not in content
