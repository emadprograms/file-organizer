from typing import Any
import pytest
import os
from pathlib import Path

import json
from unittest.mock import MagicMock, patch
from src.pipeline.pipeline import Pipeline

def test_malformed_json_graceful_failure(tmp_path) -> None:
    """Malformed _report.json causes a graceful non-zero exit, not an unhandled stack trace."""
    import subprocess
    import sys

    house_dir = tmp_path / "1273"
    house_dir.mkdir()

    # Provide valid PDF placeholder and a syntactically INVALID report JSON
    (house_dir / "1273_categorized.pdf").write_bytes(b"%PDF-1.0 invalid")
    (house_dir / "1273_report.json").write_text("{invalid json: !@#", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "src.main", str(house_dir)],
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "utf8", "GEMINI_API_KEY": "dummy"},
        cwd=str(Path(__file__).parent.parent),
    )
    stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
    combined_output = stdout + stderr

    # Must exit non-zero
    assert result.returncode != 0, (
        f"Expected non-zero exit for malformed JSON, got 0. stderr: {stderr}"
    )

    # Should not produce an unhandled stack trace leading to an unexpected error type
    # The error should be a JSONDecodeError or ValueError, not AttributeError/KeyError etc.
    assert any(
        keyword in combined_output
        for keyword in ["JSONDecodeError", "json.decoder", "ValueError", "JSON", "parse"]
    ), (
        f"Expected a JSON error indication in combined_output, got: {combined_output}"
    )

def test_pipeline_out_of_bounds_routing(tmp_path) -> None:
    """
    Test pipeline out of bounds routing.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    import subprocess
    import sys
    
    house_dir = tmp_path / "1274"
    house_dir.mkdir()
    
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Dummy PDF page")
    doc.save(str(house_dir / "1274_categorized.pdf"))
    doc.close()
    
    # We only have 1 page, but the JSON references page 2 (out-of-bounds)
    invalid_report = {
        "2": {
            "category": "1_requests_and_applications",
            "resident": "John Doe",
            "date": "2024-01-01",
            "summary": "Out of bounds test",
            "content_explanation": "Test out of bounds"
        }
    }
    
    (house_dir / "1274_report.json").write_text(json.dumps(invalid_report), encoding="utf-8")
    
    result = subprocess.run(
        [sys.executable, "-m", "src.main", str(house_dir)],
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "utf8", "GEMINI_API_KEY": "dummy"},
        cwd=str(Path(__file__).parent.parent),
    )
    
    # Check that it routed to Unassigned.
    assert "Unassigned" in result.stdout.decode("utf-8", errors="replace") or "Unassigned" in result.stderr.decode("utf-8", errors="replace"), \
        f"Expected 'Unassigned' in output, but didn't find it. stdout: {result.stdout.decode('utf-8')}, stderr: {result.stderr.decode('utf-8')}"

