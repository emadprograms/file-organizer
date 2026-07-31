import fitz
import sys
import os

def split_pdf(pdf_path, chunk_size, output_dir, prefix):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    parts = []
    
    start = 0
    part_num = 1
    
    while start < total_pages:
        end = min(start + chunk_size, total_pages)
        
        part_doc = fitz.open()
        part_doc.insert_pdf(doc, from_page=start, to_page=end-1)
        
        out_name = f"{prefix}_part{part_num}.pdf"
        out_path = os.path.join(output_dir, out_name)
        part_doc.save(out_path)
        part_doc.close()
        
        parts.append({
            "part_num": part_num,
            "file": out_path,
            "start_page_offset": start,
            "pages_in_part": end - start
        })
        
        start = end
        part_num += 1
        
    doc.close()
    return parts

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python split_pdf.py <pdf_path> <chunk_size> <output_dir> <prefix>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    chunk_size = int(sys.argv[2])
    output_dir = sys.argv[3]
    prefix = sys.argv[4]
    
    os.makedirs(output_dir, exist_ok=True)
    parts = split_pdf(pdf_path, chunk_size, output_dir, prefix)
    
    import json
    print(json.dumps(parts))
