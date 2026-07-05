import pytest
import os
from pathlib import Path

from pydantic import BaseModel
class MockPage(BaseModel):
    category: str
    residents: list[str]
    date: str
    summary: str

import json
from unittest.mock import MagicMock, patch
from src.processing.pipeline import Pipeline

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy'})
def test_pipeline_fails_fast_on_classification_error(tmp_path):
    pipeline = Pipeline("dummy_key")
    
    image_data = b"a" * 16000
    pipeline.ingestor.extract_pages_as_images = MagicMock(return_value=[(1, image_data)])
    
    pdf_path = str(tmp_path / "dummy.pdf")
    
    with patch('src.llm.llm.LLMClient.classify_page_direct') as mock_classify:
        mock_classify.side_effect = RuntimeError("API Exhausted")
        with pytest.raises(RuntimeError, match="API Exhausted"):
            pipeline.process_pdf(pdf_path)

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy'})
def test_pipeline_cache_hit(tmp_path):
    pdf_path = tmp_path / "dummy.pdf"
    cache_path = tmp_path / "dummy.pdf.cache.json"
    
    cache_data = {
        "1": {
            "category": "Housing Contract",
            "resident": "John Doe",
            "date": "2024-01-01",
            "summary": "Cache hit test"
        }
    }
    with open(cache_path, 'w') as f:
        json.dump(cache_data, f)
        
    pipeline = Pipeline("dummy_key")
    image_data = b"a" * 16000
    pipeline.ingestor.extract_pages_as_images = MagicMock(return_value=[(1, image_data)])
    
    from src.core.schemas import DocumentGroup
    dummy_group = DocumentGroup(start_page=1, end_page=1, primary_tenant="John", category="cat", dates=[], folder_path="")
    with patch('src.processing.extractors.VisionExtractor.extract_footer') as mock_vision, \
         patch('src.processing.extractors.CloudExtractor.extract') as mock_cloud, \
         patch('src.processing.pipeline.Pipeline._run_cleaning_pass', return_value={}), \
         patch('src.processing.pipeline.Pipeline._group_and_route_documents', return_value=[dummy_group]):
        
        pipeline.process_pdf(str(pdf_path))
        
        mock_vision.assert_not_called()
        mock_cloud.assert_not_called()

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy'})
def test_pipeline_interpolate_dates():
    pipeline = Pipeline("dummy_key")
    
    page1 = MockPage(category="CONTRACT", residents=["A"], date="2023-01-01", summary="")
    page2 = MockPage(category="CONTRACT", residents=["A"], date="NONE", summary="")
    page3 = MockPage(category="CONTRACT", residents=["A"], date="2023-01-05", summary="")
    page4 = MockPage(category="CONTRACT", residents=["A"], date="NONE", summary="")
    
    raw_pages = [
        (1, page1),
        (2, page2),
        (3, page3),
        (4, page4)
    ]
    
    pipeline.client.detect_date_outliers = MagicMock(return_value=[])
    
    pipeline._interpolate_dates(raw_pages, MagicMock())
    
    assert raw_pages[1][1].date == "2023-01-01"
    assert raw_pages[3][1].date == "2023-01-05"

def test_pipeline_fallback_date():
    pipeline = Pipeline("dummy_key")
    
    pipeline.ingestor.extract_pages_as_images = MagicMock(return_value=[(1, b""), (2, b"")])
    pipeline._run_cleaning_pass = MagicMock(return_value={})
    from src.core.schemas import DocumentGroup
    dummy_group = DocumentGroup(start_page=1, end_page=2, primary_tenant="A", category="forms", dates=[], folder_path="")
    pipeline._group_and_route_documents = MagicMock(return_value=[dummy_group])
    
    from src.core.schemas import UserConfig, ConfigExtraction, ConfigCleaning, ConfigGrouping, ConfigRouting, ConfigCategory
    mock_config = UserConfig(
        extraction=ConfigExtraction(prompt_template="", fields=[]),
        categories=[ConfigCategory(id="forms", name="forms")],
        cleaning=ConfigCleaning(strategy="hybrid", script_path=None, prompt_template=None, prompts={}),
        grouping=ConfigGrouping(strategy="declarative"),
        routing=ConfigRouting(strategy="declarative", rules={})
    )
    
    with patch('src.processing.pipeline.yaml.safe_load', return_value=mock_config.model_dump()), \
         patch('builtins.open', MagicMock()), \
         patch('src.core.cache.SimpleCache.__contains__', return_value=True), \
         patch('src.core.cache.SimpleCache.__getitem__', side_effect=lambda k: {"category": "forms", "resident": "A", "date": "NONE", "summary": ""}):
        pipeline.process_pdf("dummy.pdf")
        
        args, _ = pipeline._group_and_route_documents.call_args
        raw_pages_passed = args[0]
        
        assert all(page.date != "NONE" for _, page in raw_pages_passed)
        assert all(page.date is not None for _, page in raw_pages_passed)
        assert raw_pages_passed[0][1].date == "1970-01-01"

def test_pipeline_page_loss_reconciliation():
    pipeline = Pipeline("dummy_key")
    
    pipeline.ingestor.extract_pages_as_images = MagicMock(return_value=[(1, b""), (2, b""), (3, b"")])
    pipeline._run_cleaning_pass = MagicMock(return_value={})
    
    # Mocking Pass 2 to drop a page (returns group spanning 2 pages but 3 input pages exist)
    from src.core.schemas import DocumentGroup, UserConfig, ConfigExtraction, ConfigCleaning, ConfigGrouping, ConfigRouting, ConfigCategory
    bad_group = DocumentGroup(start_page=0, end_page=1, primary_tenant="A", category="forms", dates=["NONE"], folder_path="13_others")
    pipeline._group_and_route_documents = MagicMock(return_value=[bad_group])
    
    mock_config = UserConfig(
        extraction=ConfigExtraction(prompt_template="", fields=[]),
        categories=[ConfigCategory(id="forms", name="forms")],
        cleaning=ConfigCleaning(strategy="hybrid", script_path=None, prompt_template=None, prompts={}),
        grouping=ConfigGrouping(strategy="declarative"),
        routing=ConfigRouting(strategy="declarative", rules={})
    )
    
    with patch('src.processing.pipeline.yaml.safe_load', return_value=mock_config.model_dump()), \
         patch('builtins.open', MagicMock()), \
         patch('src.core.cache.SimpleCache.__contains__', return_value=True), \
         patch('src.core.cache.SimpleCache.__getitem__', side_effect=lambda k: {"category": "forms", "resident": "A", "date": "NONE", "summary": ""}):
        
        with pytest.raises(RuntimeError, match="Fatal: Page loss detected"):
            pipeline.process_pdf("dummy.pdf")


def test_malformed_json_graceful_failure(tmp_path):
    """Malformed _report.json causes a graceful non-zero exit, not an unhandled stack trace."""
    import subprocess
    import sys

    house_dir = tmp_path / "1273"
    house_dir.mkdir()

    # Provide valid PDF placeholder and a syntactically INVALID report JSON
    (house_dir / "1273_categorized.pdf").write_bytes(b"%PDF-1.0 invalid")
    (house_dir / "1273_report.json").write_text("{invalid json: !@#", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "src.organize", str(house_dir)],
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "utf8", "GEMINI_API_KEY": "dummy"},
        cwd=str(Path(__file__).parent.parent),
    )
    stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

    # Must exit non-zero
    assert result.returncode != 0, (
        f"Expected non-zero exit for malformed JSON, got 0. stderr: {stderr}"
    )

    # Should not produce an unhandled stack trace leading to an unexpected error type
    # The error should be a JSONDecodeError or ValueError, not AttributeError/KeyError etc.
    assert any(
        keyword in stderr
        for keyword in ["JSONDecodeError", "json.decoder", "ValueError", "JSON", "parse"]
    ), (
        f"Expected a JSON error indication in stderr, got: {stderr}"
    )

def test_pipeline_out_of_bounds_routing(tmp_path):
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
        [sys.executable, "-m", "src.organize", str(house_dir)],
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "utf8", "GEMINI_API_KEY": "dummy"},
        cwd=str(Path(__file__).parent.parent),
    )
    
    # Check that it routed to Unassigned.
    assert "Unassigned" in result.stdout.decode("utf-8", errors="replace") or "Unassigned" in result.stderr.decode("utf-8", errors="replace"), \
        f"Expected 'Unassigned' in output, but didn't find it. stdout: {result.stdout.decode('utf-8')}, stderr: {result.stderr.decode('utf-8')}"

