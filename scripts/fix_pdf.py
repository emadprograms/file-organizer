import pypdf
import sys

def fix_pdf(input_path, output_path):
    print(f"Reading {input_path} with pypdf...")
    try:
        reader = pypdf.PdfReader(input_path)
        print(f"Found {len(reader.pages)} pages.")
        
        writer = pypdf.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
            
        print(f"Writing to {output_path}...")
        with open(output_path, "wb") as f:
            writer.write(f)
        print("Done!")
    except Exception as e:
        print(f"Failed to fix: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_pdf.py <input> <output>")
        sys.exit(1)
    fix_pdf(sys.argv[1], sys.argv[2])
