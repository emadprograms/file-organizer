import os
import fitz  # PyMuPDF
from PIL import Image
from clean_ocr_image import clean_document_for_ocr

def main():
    # Paths
    base_dir = os.path.dirname(__file__)
    input_pdf = os.path.abspath(os.path.join(base_dir, '..', '..', 'pdfs', '1281.pdf'))
    output_pdf = os.path.abspath(os.path.join(base_dir, '..', '..', 'pdfs', '1281_cleaned.pdf'))
    temp_dir = os.path.join(base_dir, 'temp_pages')
    
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    print(f"Extracting pages from {input_pdf} using PyMuPDF...")
    
    # Open the PDF
    try:
        doc = fitz.open(input_pdf)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return

    cleaned_images = []
    
    print(f"Applying Arabic OCR pipeline to {len(doc)} pages...")
    for i in range(len(doc)):
        page = doc.load_page(i)
        # Render page to an image (dpi=300 for high quality)
        pix = page.get_pixmap(dpi=300)
        
        raw_path = os.path.join(temp_dir, f"raw_{i}.png")
        clean_path = os.path.join(temp_dir, f"cleaned_{i}.png")
        
        # Save raw image to disk
        pix.save(raw_path)
        
        # Apply the cleaner function from our script
        clean_document_for_ocr(raw_path, clean_path)
        
        # Load the cleaned image into memory for the final PDF
        if os.path.exists(clean_path):
            cleaned_img = Image.open(clean_path).convert('RGB')
            cleaned_images.append(cleaned_img)
        print(f"Finished page {i+1} of {len(doc)}")
        
    print(f"\nStitching {len(cleaned_images)} pages back into a single PDF...")
    if cleaned_images:
        cleaned_images[0].save(output_pdf, save_all=True, append_images=cleaned_images[1:])
        print(f"Success! Saved as: {output_pdf}")
    else:
        print("Error: No images were successfully processed.")
    
    # Clean up temp images
    print("Cleaning up temporary files...")
    for f in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, f))
    os.rmdir(temp_dir)

if __name__ == '__main__':
    main()
