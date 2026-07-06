"""End-to-end tests for the --dry-run pipeline mode.

Uses isolated fixture files in tests/fixtures/golden_1273/ to avoid
relying on live API calls or the main pdfs/ directory.
Pre-baked cleaned.json and grouped.json checkpoints are injected into
the tmp_path so the LLM pipeline is bypassed entirely.
"""

import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "golden_1273"

# Pre-baked cleaned.json checkpoint data (mirrors PageData schema from cleaning.py)
CLEANED_PAGES_FIXTURE = [
    {
        "category": "contract",
        "content_explanation": "Housing contract page",
        "expected_tenant_name": "Ahmed Ali",
        "expected_house_number": "1273",
        "date": "2023-01-15",
        "sender": None,
        "receiver": None,
        "subject": None,
        "canonical_tenant": "Ahmed Ali",
        "resolved_date": "2023-01-15",
        "original_index": 0,
    }
]

# Pre-baked grouped.json checkpoint data (mirrors DocumentGroup schema)
GROUPED_DOCS_FIXTURE = [
    {
        "start_page": 0,
        "end_page": 0,
        "primary_tenant": "Ahmed Ali",
        "category": "contract",
        "dates": ["2023-01-15"],
        "reason": "Single page contract",
        "brief_arabic_title": "عقد إيجار",
        "folder_path": "5_contract",
        "is_direct_routed": True,
    }
]


def _setup_dry_run_dir(tmp_path: Path) -> Path:
    """
    Create an isolated house directory with fixture PDF, report JSON, and
    pre-baked checkpoints so no LLM calls are made during --dry-run.
    Returns the house directory path.
    """
    house_dir = tmp_path / "1273"
    house_dir.mkdir()

    # Copy minimal fixture PDF
    shutil.copy(FIXTURES_DIR / "1273_categorized.pdf", house_dir / "1273_categorized.pdf")

    # Write a minimal valid report JSON (PageData format used by cleaning phase)
    report = [
        {
            "category": "contract",
            "content_explanation": "Housing contract page",
            "expected_tenant_name": "Ahmed Ali",
            "expected_house_number": "1273",
            "date": "2023-01-15",
        }
    ]
    (house_dir / "1273_report.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    # Inject pre-baked checkpoints so LLM pipeline is bypassed
    output_dir = house_dir / "output"
    output_dir.mkdir()
    cleaned_path = output_dir / "1273_cleaned.json"
    cleaned_path.write_text(json.dumps(CLEANED_PAGES_FIXTURE), encoding="utf-8")

    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_dir.mkdir()
    grouped_path = checkpoint_dir / "1273_grouped.json"
    grouped_path.write_text(json.dumps(GROUPED_DOCS_FIXTURE), encoding="utf-8")

    return house_dir


def test_dry_run_end_to_end(tmp_path):
    """
    --dry-run produces rich terminal output and does NOT create output PDFs
    or overwrite checkpoint files. Uses isolated fixtures.
    """
    house_dir = _setup_dry_run_dir(tmp_path)

    env = {**os.environ, "PYTHONIOENCODING": "utf8"}

    result = subprocess.run(
        [sys.executable, "-m", "src.organize", str(house_dir), "--output-dir", str(house_dir / "output"), "--dry-run"],
        capture_output=True,
        env=env,
        cwd=str(Path(__file__).parent.parent),  # project root
    )
    stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

    # Should exit cleanly
    assert result.returncode == 0, (
        f"--dry-run exited with {result.returncode}.\n"
        f"stdout: {stdout}\nstderr: {stderr}"
    )

    # Rich output should contain at least one of the visual indicators
    combined_output = stdout + stderr
    assert all(
        indicator in combined_output
        for indicator in ["1273", "Ahmed", "contract"]
    ), (
        f"Expected dry-run visual indicators in output, got:\n{combined_output}"
    )

    # Output directory should NOT contain generated PDFs
    output_pdf_dir = house_dir / "output" / "1273"
    assert not output_pdf_dir.exists(), (
        f"--dry-run should not create output PDF directory, but {output_pdf_dir} exists"
    )

    # Manifest should NOT be created
    manifest_path = house_dir / "output" / "1273_manifest.json"
    assert not manifest_path.exists(), (
        "--dry-run should not write manifest.json"
    )

    # Checkpoint files should remain (not deleted, since dry-run skips cleanup)
    assert (house_dir / "output" / "1273_cleaned.json").exists(), (
        "--dry-run should NOT delete cleaned.json checkpoint"
    )
    assert (house_dir / "output" / "checkpoints" / "1273_grouped.json").exists(), (
        "--dry-run should NOT delete grouped.json checkpoint"
    )
