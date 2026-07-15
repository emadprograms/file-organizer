import logging
from .extract import extract_pdf_segment
from .compress import compress_pdf

logger = logging.getLogger(f"file_organizer.{__name__}")

__all__ = ["extract_pdf_segment", "compress_pdf"]
