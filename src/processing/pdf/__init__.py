"""PDF package for extraction and compression."""

from src.processing.pdf.extract import extract_pdf_segment
from src.processing.pdf.compress import compress_pdf

__all__ = ["extract_pdf_segment", "compress_pdf"]
