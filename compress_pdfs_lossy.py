import os
import glob
import sys
import io

try:
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError:
    import subprocess
    print("Dependencies not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF", "Pillow"])
    import fitz
    from PIL import Image

def compress_pdfs(directory):
    pdf_files = [f for f in glob.glob(os.path.join(directory, "*.pdf")) if os.path.isfile(f) and not f.endswith('.tmp.pdf')]
    total_files = len(pdf_files)
    
    print(f"Found {total_files} PDF files in {directory}.")
    
    processed_list_path = os.path.join(directory, ".processed.txt")
    already_processed = set()
    if os.path.exists(processed_list_path):
        with open(processed_list_path, 'r') as f:
            already_processed = set(line.strip() for line in f)
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        
        if filename in already_processed:
            print(f"\n[{idx}/{total_files}] Skipping {filename} (Already processed in a previous run)")
            continue
            
        print(f"\n[{idx}/{total_files}] Processing: {filename}")
        
        original_size = os.path.getsize(pdf_path)
        print(f"Original size: {original_size / (1024*1024):.2f} MB")
            
        temp_output_path = pdf_path + ".tmp.pdf"
        
        try:
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                print(f"Skipping {filename}: PDF has 0 readable pages (might be corrupted or unsupported format).")
                doc.close()
                continue
                
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
                        
                        pil_img = Image.open(io.BytesIO(image_bytes))
                        
                        # Convert to RGB to save as JPEG
                        if pil_img.mode in ("RGBA", "P", "CMYK", "LA", "1", "L"):
                            pil_img = pil_img.convert("RGB")
                            
                        # Downscale large images (max 1500px on longest side)
                        # This heavily reduces size while keeping it readable (approx 150 DPI for a standard page)
                        max_dim = 1500
                        if max(pil_img.width, pil_img.height) > max_dim:
                            ratio = max_dim / float(max(pil_img.width, pil_img.height))
                            new_size = (int(pil_img.width * ratio), int(pil_img.height * ratio))
                            pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
                            
                        out = io.BytesIO()
                        # Save with 80% quality
                        pil_img.save(out, "JPEG", quality=80, optimize=True)
                        new_image_bytes = out.getvalue()
                        
                        # Only replace if the new image is actually smaller
                        if len(new_image_bytes) < len(image_bytes):
                            page.replace_image(xref, stream=new_image_bytes)
                    except Exception as e:
                        # Skip if any individual image fails to process
                        pass
                        
            # garbage=4: remove unused objects and duplicate images/fonts
            # deflate=True: compress streams
            doc.save(temp_output_path, garbage=4, deflate=True)
            doc.close()
            
            new_size = os.path.getsize(temp_output_path)
            print(f"Compressed size: {new_size / (1024*1024):.2f} MB")
            
            if new_size < original_size:
                # Replace original with compressed
                os.replace(temp_output_path, pdf_path)
                print(f"Saved {(original_size - new_size) / (1024*1024):.2f} MB.")
            else:
                # Compression didn't help (or made it larger), discard temp file
                os.remove(temp_output_path)
                print("Compression did not reduce size. Kept original file.")
                
        except Exception as e:
            print(f"Failed to process {filename}: {e}")
            if os.path.exists(temp_output_path):
                try:
                    os.remove(temp_output_path)
                except:
                    pass
            continue
            
        with open(processed_list_path, 'a') as f:
            f.write(filename + '\n')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = r"C:\Users\Emad\Documents\Safra C"
        
    compress_pdfs(target_dir)
    print("\nDone!")
