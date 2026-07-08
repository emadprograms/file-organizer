"""PDF compression utilities."""
import os
import shutil
import fitz
import logging

logger = logging.getLogger(f"file_organizer.{__name__}")

def compress_pdf(input_path: str, output_path: str):
    """Compress a PDF file by downscaling and compressing embedded images."""
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
        logger.exception(f"Compression failed for {input_path}: {e}")
        if os.path.exists(temp_output_path):
            try:
                os.remove(temp_output_path)
            except OSError:
                pass
        if input_path != output_path:
            shutil.copy2(input_path, output_path)
