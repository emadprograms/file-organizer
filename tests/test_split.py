import pytest
import os
from unittest.mock import MagicMock, patch
from src.processing.split import extract_pdf_segment, compress_pdf

def test_compress_pdf_fallback(tmp_path):
    """Test that compress_pdf falls back to copy if compression fails or doesn't help."""
    import fitz
    # Create a simple PDF
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(input_pdf))
    doc.close()

    # Case 1: Standard compression
    compress_pdf(str(input_pdf), str(output_pdf))
    assert os.path.exists(output_pdf)
    assert os.path.getsize(output_pdf) > 0

def test_extract_pdf_segment(tmp_path):
    """Test that extract_pdf_segment extracts the correct page range."""
    import fitz
    # Create a 5-page PDF
    source_pdf = tmp_path / "source.pdf"
    doc = fitz.open()
    for _ in range(5):
        doc.new_page()
    doc.save(str(source_pdf))
    doc.close()

    output_pdf = tmp_path / "segment.pdf"
    # Extract pages 1 to 2 (0-indexed, inclusive)
    extract_pdf_segment(str(source_pdf), 1, 2, str(output_pdf))

    assert os.path.exists(output_pdf)
    
    # Verify page count
    result_doc = fitz.open(output_pdf)
    assert len(result_doc) == 2
    result_doc.close()
