import fitz

def extract_pdf_segment(source_pdf: str, start_page: int, end_page: int, output_path: str):
    """
    Extracts a segment of pages from source_pdf and saves it to output_path.
    start_page and end_page are 0-indexed and inclusive.
    """
    src_doc = fitz.open(source_pdf)
    dst_doc = fitz.open()
    
    # insert_pdf arguments: from_page and to_page are 0-indexed and inclusive
    dst_doc.insert_pdf(src_doc, from_page=start_page, to_page=end_page)
    dst_doc.save(output_path)
    dst_doc.close()
    src_doc.close()
