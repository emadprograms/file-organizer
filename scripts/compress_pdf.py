import fitz
import sys
import os

def compress_pdf(input_path, output_path):
    print(f"Opening {input_path}...")
    try:
        doc = fitz.open(input_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        sys.exit(1)
        
    print(f"Compressing and saving to {output_path}...")
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    
    old_size = os.path.getsize(input_path) / (1024 * 1024)
    new_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Done! Size reduced from {old_size:.2f} MB to {new_size:.2f} MB")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compress_pdf.py <input.pdf> <output.pdf>")
        sys.exit(1)
    compress_pdf(sys.argv[1], sys.argv[2])
