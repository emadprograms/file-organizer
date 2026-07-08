"""PDF segment extraction and compression utilities.

This module handles extracting specific page ranges from a PDF and 
compressing the resulting files by downscaling images.
"""
import logging
import fitz
import os
import shutil
import io

logger = logging.getLogger(__name__)

# Suppress harmless mupdf C-level syntax warnings
fitz.TOOLS.mupdf_display_errors(False)

from src.core.indexing import to_0_based, validate_bounds

def extract_pdf_segment(source_pdf: str, start_page: int, end_page: int, output_path: str):
    """Extract a segment of pages from a PDF and save to a new file.
    
    Extracts the specified page range (0-indexed, inclusive) into a temporary
    file, applies compression, and saves the final result to `output_path`.
    
    Args:
        source_pdf (str): Path to the source PDF file.
        start_page (int): The starting page index (0-indexed, inclusive).
        end_page (int): The ending page index (0-indexed, inclusive).
        output_path (str): Path where the extracted PDF segment should be saved.
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


def compress_pdf(input_path: str, output_path: str):
    """Compress a PDF file by downscaling and compressing embedded images.
    
    Extracts large images, resizes them (max dimension 1500px), compresses
    them to JPEG, and replaces the original images. Uses a
    fallback to a simple copy if compression fails or increases file size.
    
    Args:
        input_path (str): Path to the input PDF file to compress.
        output_path (str): Path where the compressed PDF should be saved.
    """
    temp_output_path = output_path + ".tmp.pdf"
    original_size = os.path.getsize(input_path)
    
    try:
        with fitz.open(input_path) as doc:
            if len(doc) > 0:
                processed_xrefs = set()
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    image_list = page.get_images(full=True)
                    for img in image_list:
                        xref = img[0]
                        if xref in processed_xrefs:
                            continue
                        processed_xrefs.add(xref)
                        try:
                            pix = fitz.Pixmap(doc, xref)
                            if pix.n - pix.alpha > 3:
                                pix = fitz.Pixmap(fitz.csRGB, pix)
                            
                            max_dim = 1500
                            shrunk = False
                            while max(pix.width, pix.height) > max_dim:
                                pix.shrink(1)
                                shrunk = True
                                
                            image_bytes = pix.tobytes("jpeg")
                            
                            base_image = doc.extract_image(xref)
                            orig_bytes = base_image.get("image", b"")
                            
                            if len(image_bytes) < len(orig_bytes) or shrunk:
                                page.replace_image(xref, stream=image_bytes)
                        except Exception as e:
                            logger.debug(f"Skipping image compression: {e}")
                
                doc.save(temp_output_path, garbage=4, deflate=True)

        if os.path.exists(temp_output_path):
            new_size = os.path.getsize(temp_output_path)
            if new_size > 0 and new_size < original_size:
                os.replace(temp_output_path, output_path)
            else:
                os.remove(temp_output_path)
                if input_path != output_path:
                    shutil.copy2(input_path, output_path)
        else:
            if input_path != output_path:
                shutil.copy2(input_path, output_path)

    except Exception as e:
        logger.error(f"Compression failed for {input_path}: {e}")
        if os.path.exists(temp_output_path):
            try:
                os.remove(temp_output_path)
            except OSError:
                pass
        if input_path != output_path:
            shutil.copy2(input_path, output_path)
