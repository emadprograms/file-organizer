import pytest
import json
import os
from unittest.mock import MagicMock, patch
from src.pipeline import Pipeline
from src.schemas import PageClassification, Category

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy'})
def test_pipeline_fails_fast_on_classification_error(tmp_path):
    pipeline = Pipeline("dummy_key")
    
    image_data = b"a" * 16000
    pipeline.ingestor.extract_pages_as_images = MagicMock(return_value=[(1, image_data)])
    
    pdf_path = str(tmp_path / "dummy.pdf")
    
    with patch("src.llm.LLMClient.classify_page_direct") as mock_classify:
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
    
    with patch("src.extractors.VisionExtractor.extract_footer") as mock_vision, \
         patch("src.extractors.CloudExtractor.extract") as mock_cloud, \
         patch("src.pipeline.Pipeline._run_cleaning_pass", return_value={}), \
         patch("src.pipeline.Pipeline._group_pages_into_documents", return_value=[]):
        
        pipeline.process_pdf(str(pdf_path))
        
        mock_vision.assert_not_called()
        mock_cloud.assert_not_called()

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy'})
def test_pipeline_interpolate_dates():
    pipeline = Pipeline("dummy_key")
    
    page1 = PageClassification(category=Category.CONTRACT, residents=["A"], date="2023-01-01", summary="")
    page2 = PageClassification(category=Category.CONTRACT, residents=["A"], date="NONE", summary="")
    page3 = PageClassification(category=Category.CONTRACT, residents=["A"], date="2023-01-05", summary="")
    page4 = PageClassification(category=Category.CONTRACT, residents=["A"], date="NONE", summary="")
    
    raw_pages = [
        (1, page1),
        (2, page2),
        (3, page3),
        (4, page4)
    ]
    
    pipeline.client.detect_date_outliers = MagicMock(return_value=[])
    
    pipeline._interpolate_dates(raw_pages)
    
    assert raw_pages[1][1].date == "2023-01-01"
    assert raw_pages[3][1].date == "2023-01-05"
