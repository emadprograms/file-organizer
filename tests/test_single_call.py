import os
import io
from dotenv import load_dotenv
from src.ingest import PdfIngestor
from src.llm import GemmaClient
import pytest

load_dotenv()

@pytest.mark.skipif(
    "GEMINI_API_KEYS" not in os.environ,
    reason="No GEMINI_API_KEYS in env"
)
def test_single_call_integration():
    """
    Integration test that verifies a single page can be processed by the ingestor and LLM.
    This requires a real PDF file and API keys.
    """
    # Use a sample PDF if available, otherwise skip
    pdf_path = "510.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip(f"Sample PDF {pdf_path} not found")

    ingestor = PdfIngestor()
    pages = list(ingestor.extract_pages_as_images(pdf_path))
    if not pages:
        pytest.skip("No pages found in PDF")
    
    img_bytes = pages[0][1]

    client = GemmaClient(delay_between_pages=0)
    try:
        res = client.classify_page(img_bytes)
        assert res is not None
        # We don't assert specific values as the LLM output is non-deterministic
        assert hasattr(res, 'category')
        assert hasattr(res, 'residents')
        assert hasattr(res, 'is_continuation')
    except Exception as e:
        pytest.fail(f"LLM call failed: {e}")
