import pytest
from unittest.mock import MagicMock, patch
from src.processing.ingest import PdfIngestor

def test_pdf_ingestor_extraction(tmp_path):
    """Test that PdfIngestor yields pages and image bytes."""
    # Create a tiny valid PDF for testing
    import fitz
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.new_page()
    doc.save(str(pdf_path))
    doc.close()

    ingestor = PdfIngestor(dpi=72)
    pages = list(ingestor.extract_pages_as_images(str(pdf_path)))

    assert len(pages) == 2
    assert pages[0][0] == 1  # 1-indexed page index
    assert isinstance(pages[0][1], bytes)
    assert pages[1][0] == 2
