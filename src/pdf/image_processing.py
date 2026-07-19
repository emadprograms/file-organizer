"""
Image processing utilities for PDF document analysis.

This module provides functions for extracting pages from PDF documents, cleaning
them up (deskewing, illumination normalization, and diacritic boosting), and
saving them as high-quality images ready for OCR or classification.
"""
import os
import json
import logging
import fitz  # PyMuPDF
import cv2
import numpy as np

logger = logging.getLogger(__name__)

def adjust_levels(image: np.ndarray, black_point: int, white_point: int) -> np.ndarray:
    """
    Adjust the tonal range of an image by mapping the black point and white point.
    
    Args:
        image: The input image as a NumPy array.
        black_point: The pixel value to map to true black (0).
        white_point: The pixel value to map to true white (255).
        
    Returns:
        The adjusted image as a NumPy array.
    """
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        if i <= black_point:
            lut[i] = 0
        elif i >= white_point:
            lut[i] = 255
        else:
            lut[i] = int(((i - black_point) / (white_point - black_point)) * 255.0)
    return cv2.LUT(image, lut)

def auto_deskew(image: np.ndarray) -> np.ndarray:
    """
    Automatically detect and correct text skew in a grayscale image.
    
    Args:
        image: The input grayscale image as a NumPy array.
        
    Returns:
        The deskewed image, or the original image if no skew was detected
        or the skew angle was negligible.
    """
    thresh = cv2.bitwise_not(image)
    _, thresh = cv2.threshold(thresh, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return image
        
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    if abs(angle) < 0.5:
        return image
        
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def extract_and_clean_page(pdf_document: fitz.Document, page_num: int, tmp_dir: str) -> str:
    """
    Extracts a single page from a PyMuPDF document, cleans it to improve readability,
    and saves it as an image.
    
    The cleaning process includes auto-deskewing, illumination normalization,
    and diacritic boosting.
    
    Args:
        pdf_document: The opened PyMuPDF Document object.
        page_num: The 0-indexed page number to extract.
        tmp_dir: The temporary directory to save the intermediate and final images.
        
    Returns:
        The file path to the cleaned image.
        
    Raises:
        ValueError: If the raw image cannot be read from disk.
    """
    page = pdf_document.load_page(page_num)
    
    # Render page to an image (dpi=300 for high quality) exactly as in study
    pix = page.get_pixmap(dpi=300)
    
    raw_path = os.path.join(tmp_dir, f"raw_{page_num}.png")
    if os.path.exists(raw_path):
        try:
            os.remove(raw_path)
        except OSError:
            import time
            raw_path = os.path.join(tmp_dir, f"raw_{page_num}_{int(time.time()*1000)}.png")
            
    clean_path = os.path.join(tmp_dir, f"page_{page_num}.png")
    
    # Save raw image to disk exactly like process_full_pdf.py
    pix.save(raw_path)
    
    # 1. Load image in BGR
    img = cv2.imread(raw_path)
    if img is None:
        raise ValueError(f"Could not read raw image {raw_path}")
        
    # 2. Extract Green Channel
    gray = img[:, :, 1]
    
    # 3. Auto-Deskew
    # Straighten the Arabic baselines before processing
    gray = auto_deskew(gray)
    
    # 4. Estimate Background (Illumination Map)
    kernel_large = np.ones((15, 15), np.uint8)
    bg = cv2.dilate(gray, kernel_large, iterations=1)
    bg = cv2.GaussianBlur(bg, (21, 21), 0)
    
    # 5. Illumination Normalization (Division)
    # Use np.errstate to handle division by zero smoothly
    bg_float = bg.astype(np.float32)
    gray_float = gray.astype(np.float32)
    with np.errstate(divide='ignore', invalid='ignore'):
        normalized = np.where(bg_float > 0, 255.0 * (gray_float / bg_float), 255.0)
    normalized = np.clip(normalized, 0, 255).astype(np.uint8)
    
    # 6. Wash Out Light Colors ("Clean Background")
    cleaned = adjust_levels(normalized, black_point=0, white_point=220)
    
    # 7. Diacritic Boost (Black-Hat Filter)
    kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    blackhat = cv2.morphologyEx(cleaned, cv2.MORPH_BLACKHAT, kernel_small)
    boosted = cv2.subtract(cleaned, blackhat) # Darken the diacritics
    
    # 8. Sharpening (Unsharp Mask)
    gaussian = cv2.GaussianBlur(boosted, (0, 0), 2.0)
    sharpened = cv2.addWeighted(boosted, 1.5, gaussian, -0.5, 0)
    
    # Save the result
    cv2.imwrite(clean_path, sharpened)
    
    # Clean up raw image
    try:
        os.remove(raw_path)
    except OSError:
        pass
        
    return clean_path

def process_pdf(pdf_path: str, output_dir: str) -> tuple[dict, str]:
    """
    Processes all pages in a PDF, saving cleaned images to a temporary directory.
    
    This function tracks progress in a `progress.json` file to allow resuming
    interrupted processing. It performs a first pass over all pages and then
    retries any pages that failed.
    
    Args:
        pdf_path: The file path to the input PDF document.
        output_dir: The directory where the temporary folder will be created.
        
    Returns:
        A tuple containing:
            - A dictionary tracking the processing status of each page.
            - The path to the temporary directory created for this PDF.
    """
    basename = os.path.basename(pdf_path)
    tmp_dir = os.path.join(output_dir, f".tmp_{basename}")
    os.makedirs(tmp_dir, exist_ok=True)
    
    progress_file = os.path.join(tmp_dir, "progress.json")
    
    status = {}
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                status = json.load(f)
        except json.JSONDecodeError:
            pass

    def save_progress():
        tmp_progress = progress_file + ".tmp"
        with open(tmp_progress, "w", encoding="utf-8") as f:
            json.dump(status, f)
        os.replace(tmp_progress, progress_file)

    try:
        pdf_document = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {e}")
        return None, tmp_dir

    num_pages = len(pdf_document)
    
    # First pass
    for page_num in range(num_pages):
        page_key = f"page_{page_num}"
        current = status.get(page_key)
        
        if isinstance(current, dict) and (current.get("status") in ("extracted", "classified") or "category" in current):
            continue
            
        try:
            if page_num % 10 == 0:
                logger.info(f"Extracting page {page_num+1} of {num_pages} for {pdf_path}...")
            extract_and_clean_page(pdf_document, page_num, tmp_dir)
            status[page_key] = {"status": "extracted"}
        except Exception as e:
            logger.error(f"Failed to process page {page_num} of {pdf_path}: {e}")
            status[page_key] = {"status": "error", "error": str(e)}
            
        save_progress()
        
    # Retry failed pages
    for page_num in range(num_pages):
        page_key = f"page_{page_num}"
        current = status.get(page_key)
        
        if isinstance(current, dict) and current.get("status") == "error":
            try:
                if page_num % 10 == 0:
                    logger.info(f"Retrying page {page_num+1} of {num_pages} for {pdf_path}...")
                extract_and_clean_page(pdf_document, page_num, tmp_dir)
                status[page_key] = {"status": "extracted"}
            except Exception as e:
                logger.error(f"Retry failed for page {page_num} of {pdf_path}: {e}")
                status[page_key] = {"status": "error", "error": str(e)}
                
            save_progress()

    pdf_document.close()
    return status, tmp_dir
