"""Document ingestion and image extraction capabilities.

This module provides tools to read PDF files and convert their pages into images.
"""
import fitz  # PyMuPDF
from typing import Iterator, Tuple

class PdfIngestor:
    """Ingestor responsible for converting PDF pages to images for processing."""
    def __init__(self, dpi: int = 150):
        """Initialize the PdfIngestor.
        
        Args:
            dpi (int): The DPI to use when rendering PDF pages to images. Defaults to 150.
        """
        self.dpi = dpi

    def extract_pages_as_images(self, pdf_path: str) -> Iterator[Tuple[int, bytes]]:
        """Extract pages from a PDF as PNG image bytes.
        
        Args:
            pdf_path (str): The file path to the PDF document.
            
        Yields:
            Tuple[int, bytes]: A tuple containing the 1-indexed page number and the PNG image bytes.
        """
        doc = fitz.open(pdf_path)
        for page_index in range(len(doc)):
            page = doc[page_index]
            pix = page.get_pixmap(dpi=self.dpi)
            image_bytes = pix.tobytes("png")
            yield (page_index + 1, image_bytes)
