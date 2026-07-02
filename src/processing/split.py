"""PDF segment extraction and compression utilities.

This module handles extracting specific page ranges from a PDF and 
compressing the resulting files by downscaling images.
"""
import logging
import fitz
import os
logger = logging.getLogger(__name__)
import io
import shutil

try:
    from PIL import Image
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

# Suppress harmless mupdf C-level syntax warnings
fitz.TOOLS.mupdf_display_errors(False)

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
    src_doc = fitz.open(source_pdf)
    dst_doc = fitz.open()
    
    # insert_pdf arguments: from_page and to_page are 0-indexed and inclusive
    dst_doc.insert_pdf(src_doc, from_page=start_page, to_page=end_page)
    
    # Save uncompressed initially or we can compress immediately. 
    # The plan says: "Modify extract_pdf_segment in src/split.py to compress the segment before finalizing, or update the calling loop..."
    # We will save it, then compress it.
    tmp_path = output_path + ".uncompressed.pdf"
    dst_doc.save(tmp_path)
    dst_doc.close()
    src_doc.close()
    
    # Compress it
    compress_pdf(tmp_path, output_path)
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


def compress_pdf(input_path: str, output_path: str):
    """Compress a PDF file by downscaling and compressing embedded images.
    
    Extracts large images, resizes them (max dimension 1500px), compresses
    them to JPEG (80% quality), and replaces the original images. Uses a
    fallback to a simple copy if compression fails or increases file size.
    
    Args:
        input_path (str): Path to the input PDF file to compress.
        output_path (str): Path where the compressed PDF should be saved.
    """
    temp_output_path = output_path + ".tmp.pdf"
    original_size = os.path.getsize(input_path)
    
    try:
        doc = fitz.open(input_path)
        if len(doc) == 0:
            doc.close()
            if input_path != output_path:
                shutil.copy2(input_path, output_path)
            return

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
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    Image.MAX_IMAGE_PIXELS = 100_000_000  # Prevent DecompressionBomb DoS
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    if pil_img.mode in ("RGBA", "P", "CMYK", "LA", "1", "L"):
                        pil_img = pil_img.convert("RGB")  # type: ignore
                    max_dim = 1500
                    if max(pil_img.width, pil_img.height) > max_dim:
                        ratio = max_dim / float(max(pil_img.width, pil_img.height))
                        new_size = (int(pil_img.width * ratio), int(pil_img.height * ratio))  # type: ignore
                        pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)  # type: ignore
                    out = io.BytesIO()
                    pil_img.save(out, "JPEG", quality=80, optimize=True)
                    new_image_bytes = out.getvalue()
                    if len(new_image_bytes) < len(image_bytes):
                        page.replace_image(xref, stream=new_image_bytes)
                except Exception as e:
                    logger.debug(f"Skipping image compression: {e}")
        doc.save(temp_output_path, garbage=4, deflate=True)
        doc.close()
        
        new_size = os.path.getsize(temp_output_path)  # type: ignore
        if new_size < original_size:  # type: ignore
            os.replace(temp_output_path, output_path)
        else:
            os.remove(temp_output_path)
            if input_path != output_path:
                shutil.copy2(input_path, output_path)
    except Exception as e:
        logger.error(f"Compression failed for {input_path}: {e}")
        if os.path.exists(temp_output_path):
            try:
                os.remove(temp_output_path)
            except:
                pass
        if input_path != output_path:
            shutil.copy2(input_path, output_path)

