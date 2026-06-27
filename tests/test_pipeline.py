import pytest
from unittest.mock import MagicMock, patch
from src.pipeline import Pipeline

@patch("src.pipeline.SimpleCache")
def test_pipeline_fails_fast_on_classification_error(mock_cache):
    pipeline = Pipeline("dummy_key")
    pipeline.client.classify_page_direct = MagicMock(side_effect=RuntimeError("API Exhausted"))
    
    # Ensure image size > 15000 to bypass the blank page check
    image_data = b"a" * 16000
    pipeline.ingestor.extract_pages_as_images = MagicMock(return_value=[(1, image_data)])
    
    with pytest.raises(RuntimeError, match="API Exhausted"):
        pipeline.process_pdf("dummy.pdf")
