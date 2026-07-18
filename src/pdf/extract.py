"""PDF extraction utilities."""
import os
import fitz
import logging
from src.core.indexing import to_0_based, validate_bounds
from src.pdf.compress import compress_pdf

logger = logging.getLogger(f"file_organizer.{__name__}")

def extract_pdf_segment(source_pdf: str, start_page: int, end_page: int, output_path: str) -> None:
    """Extract a segment of pages from a PDF and save to a new file.

    Extracts a page range (inclusive) from the source PDF, saves it to a 
    temporary file, and then applies compression before finalizing the output.

    Args:
        source_pdf (str): Path to the source PDF file.
        start_page (int): The 0-based index of the starting page.
        end_page (int): The 0-based index of the ending page.
        output_path (str): The target path for the extracted PDF segment.
    """
    start_0 = to_0_based(start_page + 1)
    end_0 = to_0_based(end_page + 1)
    tmp_path = output_path + ".uncompressed.pdf"
    
    with fitz.open(source_pdf) as src_doc:
        max_len = len(src_doc)
        start_idx = validate_bounds(start_0, max_len)
        end_idx = validate_bounds(end_0, max_len)
        
        with fitz.open() as dst_doc:
            dst_doc.insert_pdf(src_doc, from_page=start_idx, to_page=end_idx)
            dst_doc.save(tmp_path)
    
    # Compress it
    compress_pdf(tmp_path, output_path)
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
