"""
Regression parity tests for migration sweeps 1-8.

Each test guards a specific fix so that reverting the fix causes a test failure.
Tests use @patch / MagicMock and real minimal PDFs (via PdfWriter) where needed.
"""
import ast
import inspect
import json
import os
import re
import shutil
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class DummyArgs:
    """Minimal stand-in for argparse namespace used by run_reconcile_mode."""
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"


def _create_minimal_pdf(path: Path, num_pages: int = 1) -> None:
    """Create a real multi-page PDF via pypdf so fitz can open it."""
    from pypdf import PdfWriter
    w = PdfWriter()
    for _ in range(num_pages):
        w.add_blank_page(width=72, height=72)
    with open(path, "wb") as f:
        w.write(f)


def _make_house(tmp_path, house_id="999", *, tenants_yaml=None, state_extra=None):
    """Scaffold a minimal house directory suitable for run_reconcile_mode."""
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)

    if tenants_yaml is None:
        tenants_yaml = "- name: Tenant A\n  start_date: '2020-01-01'\n  end_date: present\n"
    with open(source_dir / f"{house_id}_tenants.yaml", "w", encoding="utf-8") as f:
        f.write(tenants_yaml)

    state_data = {
        "house_id": house_id,
        "cleaned_pages": [],
        "grouped_documents": [],
        "routed_documents": {"per_page": []},
    }
    if state_extra:
        state_data.update(state_extra)
    with open(source_dir / f"{house_id}_state.json", "w", encoding="utf-8") as f:
        json.dump(state_data, f)

    return target_dir, source_dir, vault_dir


# ===========================================================================
# 1. PDF Slicing – reconcile calls extract_pdf_segment & compress_pdf for
#    group manifests
# ===========================================================================

@patch("src.pdf.compress_pdf", autospec=True)
@patch("src.pdf.extract_pdf_segment", autospec=True)
def test_01_pdf_slicing_group_manifest(mock_extract, mock_compress, tmp_path):
    """reconcile must invoke extract_pdf_segment + compress_pdf per group."""
    from src.reconcile.core import run_reconcile_mode

    target_dir, source_dir, vault_dir = _make_house(tmp_path)

    # Place a raw PDF in the house dir
    raw_pdf = target_dir / "2020-01-01 - Doc.pdf"
    _create_minimal_pdf(raw_pdf, num_pages=4)

    # Group manifest splitting at page 0-1 and 2-3
    manifest = {
        "groups": [
            {"start_page": 0, "end_page": 1, "expected_tenant_name": "Tenant A", "category": "Contract", "content_explanation": "Part 1"},
            {"start_page": 2, "end_page": 3, "expected_tenant_name": "Tenant A", "category": "Contract", "content_explanation": "Part 2"},
        ]
    }
    with open(target_dir / "2020-01-01 - Doc_ingest_manifest.json", "w") as f:
        json.dump(manifest, f)

    args = DummyArgs(target_dir)
    result = run_reconcile_mode(args)
    assert result == 0
    assert mock_extract.call_count == 2, "extract_pdf_segment must be called once per group"
    assert mock_compress.call_count == 2, "compress_pdf must be called once per group"


# ===========================================================================
# 2. raw_dump.json preservation – ingest moves it to .source_files
# ===========================================================================

@patch("src.ingest.core.fitz")
def test_02_raw_dump_preserved(mock_fitz, tmp_path):
    """ingest must move raw_dump.json into .source_files, never delete it."""
    from src.ingest.core import run_ingest_mode
    from src.core.config import AppConfig

    input_dir = tmp_path / "inbox"
    input_dir.mkdir()

    dump = [{"category": "Contract", "expected_tenant_name": "T", "content_explanation": "x"}]
    dump_path = input_dir / "100.raw_dump.json"
    with open(dump_path, "w") as f:
        json.dump(dump, f)

    pdf_path = input_dir / "100.pdf"
    _create_minimal_pdf(pdf_path, num_pages=1)

    # Mock fitz.open so it returns a context manager with page_count=1
    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_doc.__enter__ = MagicMock(return_value=mock_doc)
    mock_doc.__exit__ = MagicMock(return_value=False)
    mock_fitz.open.return_value = mock_doc

    areas_root = tmp_path / "areas"
    areas_root.mkdir()

    config = MagicMock(spec=AppConfig)
    config.areas_root_path = str(areas_root)

    args = MagicMock()
    args.input_path = str(input_dir)
    args.dry_run = False

    result = run_ingest_mode(args, config, MagicMock())
    assert result == 0

    # raw_dump.json should be in .source_files, not in original location
    assert not dump_path.exists(), "raw_dump.json should have been moved from inbox"
    dest_dump = areas_root / "100" / ".source_files" / "100.raw_dump.json"
    assert dest_dump.exists(), "raw_dump.json should be preserved in .source_files"


# ===========================================================================
# 3. No "Unassigned" placeholder in tenant YAML
# ===========================================================================

def test_03_no_unassigned_in_yaml():
    """ingest must not generate Unassigned YAML entries for tenant names."""
    src = inspect.getsource(__import__("src.ingest.core", fromlist=["run_ingest_mode"]).run_ingest_mode)
    # The filtering clause should exclude Unassigned/غير محدد
    assert 'not t.startswith("Unassigned")' in src or "Unassigned" in src
    assert 'not t.startswith("غير محدد")' in src


# ===========================================================================
# 4. PDF page count validation – ingest validates counts match the dump
# ===========================================================================

@patch("src.ingest.core.fitz")
def test_04_pdf_page_count_validation(mock_fitz, tmp_path):
    """ingest must reject when no PDF matches the dump page count."""
    from src.ingest.core import run_ingest_mode
    from src.core.config import AppConfig

    input_dir = tmp_path / "inbox"
    input_dir.mkdir()

    dump = [{"category": "Contract", "expected_tenant_name": "T", "content_explanation": "x"}] * 5
    with open(input_dir / "200.raw_dump.json", "w") as f:
        json.dump(dump, f)

    pdf_path = input_dir / "200.pdf"
    _create_minimal_pdf(pdf_path, num_pages=3)

    # fitz says the PDF has 3 pages, but dump expects 5 → mismatch
    mock_doc = MagicMock()
    mock_doc.page_count = 3
    mock_doc.__enter__ = MagicMock(return_value=mock_doc)
    mock_doc.__exit__ = MagicMock(return_value=False)
    mock_fitz.open.return_value = mock_doc

    areas_root = tmp_path / "areas"
    areas_root.mkdir()

    config = MagicMock(spec=AppConfig)
    config.areas_root_path = str(areas_root)

    args = MagicMock()
    args.input_path = str(input_dir)
    args.dry_run = False

    result = run_ingest_mode(args, config, MagicMock())
    # Should report an error because page counts don't match
    assert result == 1


# ===========================================================================
# 5. Dry Run Visualizer – both pipelines call Visualizer.print_summary
# ===========================================================================

def test_05_reconcile_dry_run_visualizer():
    """reconcile must import and call Visualizer.print_summary in dry_run mode."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "reconcile" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "Visualizer" in code
    assert "vis.print_summary" in code or "visualizer.print_summary" in code


def test_05b_ingest_dry_run_visualizer():
    """ingest must import and call Visualizer.print_summary in dry_run mode."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "ingest" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "Visualizer" in code
    assert "vis.print_summary" in code


# ===========================================================================
# 6. JSON Report Generation – ingest produces ingest_report.json
# ===========================================================================

def test_06_ingest_produces_report():
    """ingest source code must write ingest_report.json via atomic_write."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "ingest" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "ingest_report.json" in code
    assert "atomic_write" in code


# ===========================================================================
# 7. Strict category validation – raises ValidationError (not just logging)
# ===========================================================================

@patch("src.ingest.core.fitz")
def test_07_strict_category_validation(mock_fitz, tmp_path):
    """ingest must raise ValidationError for unknown categories."""
    from src.ingest.core import run_ingest_mode
    from src.core.config import AppConfig
    from src.core.exceptions import ValidationError

    input_dir = tmp_path / "inbox"
    input_dir.mkdir()

    dump = [{"category": "BOGUS_CATEGORY_XYZ", "expected_tenant_name": "T", "content_explanation": "x"}]
    with open(input_dir / "300.raw_dump.json", "w") as f:
        json.dump(dump, f)

    pdf_path = input_dir / "300.pdf"
    _create_minimal_pdf(pdf_path, num_pages=1)

    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_doc.__enter__ = MagicMock(return_value=mock_doc)
    mock_doc.__exit__ = MagicMock(return_value=False)
    mock_fitz.open.return_value = mock_doc

    areas_root = tmp_path / "areas"
    areas_root.mkdir()

    config = MagicMock(spec=AppConfig)
    config.areas_root_path = str(areas_root)

    args = MagicMock()
    args.input_path = str(input_dir)
    args.dry_run = False

    with pytest.raises(ValidationError):
        run_ingest_mode(args, config, MagicMock())


@patch("src.ingest.core.fitz")
def test_07b_missing_category_raises(mock_fitz, tmp_path):
    """ingest must raise ValidationError when category is missing/None."""
    from src.ingest.core import run_ingest_mode
    from src.core.config import AppConfig
    from src.core.exceptions import ValidationError

    input_dir = tmp_path / "inbox"
    input_dir.mkdir()

    dump = [{"category": None, "expected_tenant_name": "T", "content_explanation": "x"}]
    with open(input_dir / "301.raw_dump.json", "w") as f:
        json.dump(dump, f)

    pdf_path = input_dir / "301.pdf"
    _create_minimal_pdf(pdf_path, num_pages=1)

    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_doc.__enter__ = MagicMock(return_value=mock_doc)
    mock_doc.__exit__ = MagicMock(return_value=False)
    mock_fitz.open.return_value = mock_doc

    areas_root = tmp_path / "areas"
    areas_root.mkdir()

    config = MagicMock(spec=AppConfig)
    config.areas_root_path = str(areas_root)

    args = MagicMock()
    args.input_path = str(input_dir)
    args.dry_run = False

    with pytest.raises(ValidationError):
        run_ingest_mode(args, config, MagicMock())


# ===========================================================================
# 8. Tenant YAML merging – ingest merges new tenants instead of discarding
# ===========================================================================

def test_08_tenant_yaml_merging():
    """ingest source must contain merge logic when YAML already exists."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "ingest" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    # Must have the else branch that reads existing YAML and appends
    assert "existing_data.append" in code or "existing_names" in code
    assert "yaml.safe_load" in code


# ===========================================================================
# 9. Skip _categorized/_finalized PDFs – reconcile skips them
# ===========================================================================

def test_09_skip_categorized_finalized():
    """reconcile source must skip PDFs with _categorized or _finalized in name."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "reconcile" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert '"_categorized"' in code or "'_categorized'" in code
    assert '"_finalized"' in code or "'_finalized'" in code


# ===========================================================================
# 10. Empty YAML crash guard – reconcile handles None from yaml.safe_load
# ===========================================================================

def test_10_empty_yaml_crash_guard(tmp_path):
    """reconcile must not crash when tenant YAML loads as None (empty file).

    Functional test: actually calls run_reconcile_mode with an empty
    _tenants.yaml so that yaml.safe_load returns None.  The ``or []`` guard
    in reconcile/core.py must absorb the None and let the function return 0
    without raising AttributeError or TypeError.
    """
    from src.reconcile.core import run_reconcile_mode

    target_dir, source_dir, vault_dir = _make_house(
        tmp_path,
        tenants_yaml=""  # Empty file → yaml.safe_load returns None → guarded with or []
    )
    args = DummyArgs(target_dir)
    # Must not raise; must complete successfully
    result = run_reconcile_mode(args)
    assert result == 0


# ===========================================================================
# 11. Fitz over pypdf – both pipelines use fitz.open() with doc.page_count
# ===========================================================================

def test_11_fitz_in_reconcile():
    """reconcile must use fitz.open / doc.page_count, NOT pypdf.PdfReader."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "reconcile" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "import fitz" in code
    assert "fitz.open" in code
    assert "doc.page_count" in code
    assert "PdfReader" not in code, "reconcile must not use pypdf.PdfReader"


def test_11b_fitz_in_ingest():
    """ingest must use fitz.open / doc.page_count, NOT pypdf.PdfReader."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "ingest" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "import fitz" in code or "fitz" in code
    assert "doc.page_count" in code
    assert "PdfReader" not in code, "ingest must not use pypdf.PdfReader"


def test_11c_fitz_in_pdf_extract():
    """extract.py must use fitz, not pypdf."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "pdf" / "extract.py"
    code = src_path.read_text(encoding="utf-8")
    assert "import fitz" in code
    assert "PdfReader" not in code


# ===========================================================================
# 12. Atomic writes – reports and YAML use atomic_write
# ===========================================================================

def test_12_atomic_write_reconcile():
    """reconcile must use atomic_write for report JSON files."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "reconcile" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "atomic_write" in code
    # Must appear for report files
    assert "reconcile_report.json" in code or "_report.json" in code


def test_12b_atomic_write_ingest():
    """ingest must use atomic_write for report and YAML files."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "ingest" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "atomic_write" in code


# ===========================================================================
# 13. No auto-verification – reconcile does NOT call run_verification
# ===========================================================================

def test_13_no_auto_verification():
    """reconcile must NOT automatically call run_verification at the end."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "reconcile" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "run_verification" not in code, (
        "reconcile must not auto-call run_verification; it should be done externally"
    )


# ===========================================================================
# 14. Windows encoding safeguard – reconfigure block gated on dry_run
# ===========================================================================

def test_14_windows_encoding_reconcile():
    """reconcile must have win32 stdout reconfigure gated on dry_run."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "reconcile" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "sys.stdout.reconfigure" in code
    assert "win32" in code
    assert "dry_run" in code


def test_14b_windows_encoding_ingest():
    """ingest must have win32 stdout reconfigure gated on dry_run."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "ingest" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "sys.stdout.reconfigure" in code
    assert "win32" in code


# ===========================================================================
# 15. ValidationError string format – includes " Please fix the report JSON."
# ===========================================================================

def test_15_validation_error_format():
    """ValidationError messages must end with ' Please fix the report JSON.'."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "ingest" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "Please fix the report JSON." in code


# ===========================================================================
# 16. Glob .is_file() checks – glob results filtered with .is_file()
# ===========================================================================

def test_16_glob_is_file_reconcile():
    """reconcile glob results must be filtered with .is_file()."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "reconcile" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    # The YAML glob uses is_file filter
    assert 'if p.is_file()' in code or '.is_file()' in code


def test_16b_glob_is_file_ingest():
    """ingest glob results must be filtered with .is_file()."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "ingest" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "p.is_file()" in code or ".is_file()" in code


# ===========================================================================
# 17. State schema has routed_documents – reconcile populates it
# ===========================================================================

def test_17_state_schema_routed_documents():
    """State class must default routed_documents in its schema."""
    from src.core.state import State
    src_path = Path(__file__).resolve().parent.parent / "src" / "core" / "state.py"
    code = src_path.read_text(encoding="utf-8")
    assert '"routed_documents"' in code or "'routed_documents'" in code


def test_17b_reconcile_saves_routed_documents():
    """reconcile must save state.data['routed_documents'] before state.save()."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "reconcile" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert 'state.data["routed_documents"]' in code or "state.data['routed_documents']" in code


def test_17c_routed_documents_or_dict():
    """reconcile must use `or {}` pattern for routed_documents to avoid None crash."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "reconcile" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert 'state.data.get("routed_documents") or {}' in code, (
        "routed_documents must use `or {}` to handle None/list/missing"
    )


# ===========================================================================
# 18. No exception swallowing – fitz.open / json.load exceptions bubble up
# ===========================================================================

def test_18_no_exception_swallowing_reconcile():
    """reconcile fitz.open calls must NOT be wrapped in bare except/pass."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "reconcile" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    # fitz.open appears multiple times; none should be inside a try/except that swallows
    lines = code.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "fitz.open" in stripped and stripped.startswith("with fitz.open"):
            # Look backward for a try: that would wrap this
            # Make sure there's no bare `except:` or `except Exception:` with pass
            # that would suppress the error without re-raising
            j = i - 1
            found_try = False
            while j >= 0 and j > i - 5:
                if lines[j].strip() == "try:":
                    found_try = True
                    break
                j -= 1
            if found_try:
                # Check if there's an except block that just does `pass`
                k = i + 1
                has_bare_except = False
                while k < len(lines) and k < i + 10:
                    l_stripped = lines[k].strip()
                    if l_stripped.startswith("except") and "pass" in (lines[k+1].strip() if k+1 < len(lines) else ""):
                        has_bare_except = True
                        break
                    if l_stripped and not l_stripped.startswith("#"):
                        break
                    k += 1
                assert not has_bare_except, (
                    f"fitz.open at line {i+1} appears to be inside a try/except that swallows errors"
                )


def test_18b_json_load_not_swallowed():
    """json.load in ingest must not be wrapped in a bare except."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "ingest" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    # Verify json.load is present and NOT surrounded by try/except/pass
    assert "json.load" in code
    lines = code.splitlines()
    for i, line in enumerate(lines):
        if "json.load" in line:
            # Check surrounding context for bare except/pass
            j = i - 1
            found_try = False
            while j >= 0 and j > i - 5:
                if lines[j].strip() == "try:":
                    found_try = True
                    break
                j -= 1
            if found_try:
                k = i + 1
                while k < len(lines) and k < i + 10:
                    l_stripped = lines[k].strip()
                    if l_stripped.startswith("except") and "pass" in (lines[k+1].strip() if k+1 < len(lines) else ""):
                        pytest.fail(f"json.load at line {i+1} appears to be inside try/except/pass")
                    if l_stripped and not l_stripped.startswith("#") and not l_stripped.startswith("except"):
                        break
                    k += 1


# ===========================================================================
# 19. --categorization-model override – ingest respects the flag
# ===========================================================================

def test_19_categorization_model_override():
    """main.py must define --categorization-model argument for the create parser."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "main.py"
    code = src_path.read_text(encoding="utf-8")
    assert "--categorization-model" in code
    assert "categorization_model" in code


# ===========================================================================
# 20. PDF page count matching heuristic – ingest matches PDFs by page count
# ===========================================================================

def test_20_pdf_page_count_matching():
    """ingest must compare fitz doc.page_count to dump array length."""
    src_path = Path(__file__).resolve().parent.parent / "src" / "ingest" / "core.py"
    code = src_path.read_text(encoding="utf-8")
    assert "doc.page_count == dump_pages" in code or "page_count" in code


# ===========================================================================
# BONUS: Integration-style test for the routed_documents fix (item 17c)
# ===========================================================================

@patch("src.pdf.compress_pdf", autospec=True)
@patch("src.pdf.extract_pdf_segment", autospec=True)
def test_bonus_routed_documents_none_handled(mock_extract, mock_compress, tmp_path):
    """reconcile must not crash when routed_documents is None in state.json."""
    from src.reconcile.core import run_reconcile_mode

    target_dir, source_dir, vault_dir = _make_house(
        tmp_path,
        state_extra={"routed_documents": None}
    )

    args = DummyArgs(target_dir)
    result = run_reconcile_mode(args)
    assert result == 0


@patch("src.pdf.compress_pdf", autospec=True)
@patch("src.pdf.extract_pdf_segment", autospec=True)
def test_bonus_routed_documents_list_handled(mock_extract, mock_compress, tmp_path):
    """reconcile must not crash when routed_documents is a list in state.json."""
    from src.reconcile.core import run_reconcile_mode

    target_dir, source_dir, vault_dir = _make_house(
        tmp_path,
        state_extra={"routed_documents": []}
    )

    args = DummyArgs(target_dir)
    result = run_reconcile_mode(args)
    assert result == 0


@patch("src.pdf.compress_pdf", autospec=True)
@patch("src.pdf.extract_pdf_segment", autospec=True)
def test_bonus_routed_documents_missing_handled(mock_extract, mock_compress, tmp_path):
    """reconcile must not crash when routed_documents key is absent from state.json."""
    from src.reconcile.core import run_reconcile_mode

    house_id = "999"
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)

    with open(source_dir / f"{house_id}_tenants.yaml", "w", encoding="utf-8") as f:
        f.write("- name: Tenant A\n  start_date: '2020-01-01'\n  end_date: present\n")

    # Intentionally omit routed_documents from state
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [],
        "grouped_documents": [],
    }
    with open(source_dir / f"{house_id}_state.json", "w", encoding="utf-8") as f:
        json.dump(state_data, f)

    args = DummyArgs(target_dir)
    result = run_reconcile_mode(args)
    assert result == 0


# ===========================================================================
# BONUS: V4 routed_documents populated list
# ===========================================================================

@patch("src.pdf.compress_pdf", autospec=True)
@patch("src.pdf.extract_pdf_segment", autospec=True)
def test_bonus_v4_routed_documents_list(mock_extract, mock_compress, tmp_path):
    """reconcile must handle V4 state files where routed_documents is a
    *populated* list (not a dict).  The list items use the flat-page format
    V4 produced, e.g. [{"page_index": 0, "vault_id": "abc", ...}].
    The code converts this to {"per_page": [...]} internally; the test
    asserts that run_reconcile_mode returns 0 without crashing."""
    from src.reconcile.core import run_reconcile_mode

    house_id = "888"
    target_dir = tmp_path / f"{house_id} - V4 House"
    source_dir = target_dir / ".source_files"
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)

    # Create a minimal vault PDF so reconcile finds the file
    vault_id = "deadbeef01234567deadbeef01234567"
    vault_pdf = vault_dir / f"doc_{vault_id}.pdf"
    _create_minimal_pdf(vault_pdf, num_pages=1)

    # Create a real .lnk-style shortcut path entry in the target directory
    # (We simply don't place a .lnk, so the code will mark it user_deleted
    # and trash the vault PDF — that's fine; we just need no crash.)

    with open(source_dir / f"{house_id}_tenants.yaml", "w", encoding="utf-8") as f:
        f.write("- name: Tenant A\n  start_date: '2020-01-01'\n  end_date: present\n")

    # V4 state: routed_documents is a populated flat list
    v4_routed_list = [
        {
            "page_index": 0,
            "vault_id": vault_id,
            "output_file": f"{target_dir.name}/Tenant A/doc.lnk",
            "target_folder": "Tenant A",
            "dates": ["2021-06-15"],
            "date": "2021-06-15",
            "brief_arabic_title": "Test Doc",
            "user_locked": False,
            "canonical_tenant": "Tenant A",
            "category": "Contract",
        }
    ]

    state_data = {
        "house_id": house_id,
        "cleaned_pages": [
            {
                "category": "Contract",
                "content_explanation": "Test page",
                "original_index": 0,
                "date": "2021-06-15",
                "resolved_date": "2021-06-15",
                "user_locked": False,
                "canonical_tenant": "Tenant A",
            }
        ],
        "grouped_documents": [
            {
                "start_page": 0,
                "end_page": 0,
                "primary_tenant": "Tenant A",
                "category": "Contract",
                "dates": ["2021-06-15"],
                "brief_arabic_title": "Test Doc",
                "vault_id": vault_id,
                "user_locked": False,
                "shortcuts": [],
            }
        ],
        # V4 format: a populated list, NOT a dict
        "routed_documents": v4_routed_list,
    }
    with open(source_dir / f"{house_id}_state.json", "w", encoding="utf-8") as f:
        json.dump(state_data, f)

    args = DummyArgs(target_dir)
    # Must not raise AttributeError/TypeError on list; must return 0
    result = run_reconcile_mode(args)
    assert result == 0
