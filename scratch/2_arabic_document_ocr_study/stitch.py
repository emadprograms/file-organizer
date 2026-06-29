import fitz
import os

def main():
    base_dir = os.path.dirname(__file__)
    temp_dir = os.path.join(base_dir, 'temp_pages')
    output_pdf = os.path.abspath(os.path.join(base_dir, '..', '..', 'pdfs', '1281_cleaned.pdf'))

    doc = fitz.open()

    print("Stitching 209 cleaned images into a PDF using PyMuPDF...")
    for i in range(209):
        clean_path = os.path.join(temp_dir, f"cleaned_{i}.png")
        if os.path.exists(clean_path):
            try:
                img_doc = fitz.open(clean_path)
                pdf_bytes = img_doc.convert_to_pdf()
                pdf_doc = fitz.open("pdf", pdf_bytes)
                doc.insert_pdf(pdf_doc)
                img_doc.close()
                pdf_doc.close()
            except Exception as e:
                print(f"Error on page {i}: {e}")
        else:
            print(f"Missing page {i}")

    print(f"Saving to {output_pdf}...")
    doc.save(output_pdf)
    doc.close()
    
    print("Done! Cleaning up temp files...")
    for f in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, f))
    os.rmdir(temp_dir)
    print("Cleanup complete!")

if __name__ == '__main__':
    main()
