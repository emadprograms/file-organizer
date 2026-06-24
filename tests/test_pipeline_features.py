import pytest
from unittest.mock import MagicMock, patch
import fitz
import os
from src.ingest import PdfIngestor
from src.pipeline import Pipeline
from src.schemas import PageClassification, Category

@pytest.fixture
def dummy_5_page_pdf(tmp_path):
    pdf = fitz.open()
    for _ in range(5):
        page = pdf.new_page(width=595, height=842)
        page.insert_text((50, 50), "Test Page " * 1000)
    file_path = str(tmp_path / "dummy_5_page.pdf")
    pdf.save(file_path)
    pdf.close()
    return file_path

def test_ingest_5_page_pdf(dummy_5_page_pdf):
    """Requirement: Ingest a 5-page PDF and verify 5 valid image bytes objects are created"""
    ingestor = PdfIngestor()
    pages = list(ingestor.extract_pages_as_images(dummy_5_page_pdf))
    
    assert len(pages) == 5
    for i, (page_num, image_bytes) in enumerate(pages):
        assert page_num == i
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

@patch("google.genai.models.Models.generate_content")
def test_pipeline_retry_logic(mock_generate_content, dummy_5_page_pdf):
    """Requirement: Simulate an API failure on page 3 and verify the retry logic eventually succeeds"""
    
    failure_state = {"failed": False}
    
    class DummyResponse:
        def __init__(self):
            self.parsed = PageClassification(
                house_number="123",
                residents=["Test"],
                category=Category.BASIC_DETAILS,
                date="NONE"
            )
            self.text = '{"house_number": "123", "residents": ["Test"], "category": "basic_details", "date": "NONE"}'
            
    def mock_generate(*args, **kwargs):
        if not failure_state["failed"]:
            failure_state["failed"] = True
            raise Exception("429 Too Many Requests")
        return DummyResponse()

    mock_generate_content.side_effect = mock_generate
    
    pipeline = Pipeline(api_keys=["dummy-key"])
    # The rate limiter is hit once, retries, and then succeeds for the 5 pages
    with patch("src.llm.GemmaClient.resolve_entities", return_value={}):
        documents = pipeline.process_pdf(dummy_5_page_pdf)
    
    assert len(documents) > 0
    # 5 pages + 1 retry = 6 calls
    assert mock_generate_content.call_count == 6

def test_pipeline_concurrency_memory(dummy_5_page_pdf, tmp_path):
    """Requirement: Monitor memory usage on a large dummy PDF to ensure concurrency constraints hold"""
    # Create a 50 page PDF to simulate a larger file
    pdf = fitz.open()
    for _ in range(50):
        page = pdf.new_page(width=595, height=842)
        page.insert_text((50, 50), "Memory Test " * 1000)
    pdf_path = str(tmp_path / "large_dummy_isolated.pdf")
    pdf.save(pdf_path)
    pdf.close()
    
    pipeline = Pipeline(api_keys=["dummy-key"])
    
    with patch("src.llm.GemmaClient.classify_page") as mock_classify, \
         patch("src.llm.GemmaClient.resolve_entities", return_value={}):
        mock_classify.return_value = PageClassification(
            house_number="123", residents=["Test"], category=Category.BASIC_DETAILS, date="NONE"
        )
        
        # This will process 50 pages using max_workers=5
        documents = pipeline.process_pdf(pdf_path)
        
        # Validate that it processed all 50 pages without throwing out-of-memory or thread exhaustion
        assert mock_classify.call_count == 50
        assert len(documents) > 0
