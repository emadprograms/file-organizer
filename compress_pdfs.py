import os
import glob
import sys
import shutil

try:
    import fitz  # PyMuPDF
except ImportError:
    import subprocess
    print("PyMuPDF not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF"])
    import fitz

def compress_pdfs(directory):
    pdf_files = [f for f in glob.glob(os.path.join(directory, "*.pdf")) if os.path.isfile(f)]
    total_files = len(pdf_files)
    
    print(f"Found {total_files} PDF files in {directory}.")
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        print(f"\n[{idx}/{total_files}] Processing: {filename}")
        
        original_size = os.path.getsize(pdf_path)
        print(f"Original size: {original_size / (1024*1024):.2f} MB")
        
        temp_output_path = pdf_path + ".tmp.pdf"
        
        try:
            doc = fitz.open(pdf_path)
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
            print(f"Failed to compress {filename}: {e}")
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)

if __name__ == "__main__":
    target_dir = r"C:\Users\Emad\Documents\Safra C"
    compress_pdfs(target_dir)
    print("\nDone!")
