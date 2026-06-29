import cv2
import numpy as np
import os

def adjust_levels(image, black_point, white_point):
    """
    Simulates a 'Clean Background' photocopy feature using a Levels adjustment.
    Values <= black_point become pure black (0).
    Values >= white_point become pure white (255).
    Values in between are linearly stretched, preserving anti-aliasing.
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

def auto_deskew(image):
    """
    Detects the tilt of the text and rotates the image to make the baseline perfectly horizontal.
    """
    # Threshold to find text blobs
    thresh = cv2.bitwise_not(image)
    _, thresh = cv2.threshold(thresh, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # Get all text pixel coordinates
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return image
        
    # Calculate the minimum bounding box and its angle
    angle = cv2.minAreaRect(coords)[-1]
    
    # Adjust angle to be between -45 and 45
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    # If the angle is very small, it's likely already straight
    if abs(angle) < 0.5:
        return image
        
    # Rotate the image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    # Use BORDER_REPLICATE so the edges remain white/background colored
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def clean_document_for_ocr(image_path, output_path):
    # 1. Load image in BGR
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image {image_path}")
        return

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
    normalized = 255 * (gray.astype(np.float32) / bg.astype(np.float32))
    normalized = np.clip(normalized, 0, 255).astype(np.uint8)
    
    # 6. Wash Out Light Colors ("Clean Background")
    cleaned = adjust_levels(normalized, black_point=0, white_point=220)
    
    # 7. Diacritic Boost (Black-Hat Filter)
    # Applying this after washout perfectly isolates the small dark dots
    # against the pure white background, deepening them cleanly.
    kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    blackhat = cv2.morphologyEx(cleaned, cv2.MORPH_BLACKHAT, kernel_small)
    boosted = cv2.subtract(cleaned, blackhat) # Darken the diacritics
    
    # 8. Sharpening (Unsharp Mask)
    gaussian = cv2.GaussianBlur(boosted, (0, 0), 2.0)
    sharpened = cv2.addWeighted(boosted, 1.5, gaussian, -0.5, 0)
    
    # Save the result
    cv2.imwrite(output_path, sharpened)
    print(f"Cleaned image saved to {output_path}")

if __name__ == "__main__":
    input_img = "page-15.png"
    output_img = "page-15_cleaned.png"
    
    if os.path.exists(input_img):
        clean_document_for_ocr(input_img, output_img)
    else:
        print(f"Error: {input_img} not found.")
