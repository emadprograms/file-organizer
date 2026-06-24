import fitz  # PyMuPDF
from typing import Iterator, Tuple

class PdfIngestor:
    def __init__(self, dpi: int = 150):
        self.dpi = dpi

    def extract_pages_as_images(self, pdf_path: str) -> Iterator[Tuple[int, bytes]]:
        """Yields (page_index, image_bytes) for each page in the PDF, 1-indexed."""
        doc = fitz.open(pdf_path)
        for page_index in range(len(doc)):
            page = doc[page_index]
            pix = page.get_pixmap(dpi=self.dpi)
            image_bytes = pix.tobytes("png")
            yield (page_index + 1, image_bytes)
