import os
import sys
from dotenv import load_dotenv

# Ensure we're in the right directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.pipeline import Pipeline

def test_first_10_pages():
    load_dotenv()
    api_keys_str = os.getenv("GEMINI_API_KEYS")
    api_keys = [k.strip() for k in api_keys_str.split(",")] if api_keys_str else None
    if not api_keys:
        print("Please set GEMINI_API_KEYS in .env")
        return

    pipeline = Pipeline(api_keys=api_keys)
    
    # Patch extract_pages_as_images to only yield 10 pages
    original_extract = pipeline.ingestor.extract_pages_as_images
    
    def mocked_extract(pdf_path):
        gen = original_extract(pdf_path)
        for _ in range(10):
            try:
                yield next(gen)
            except StopIteration:
                break
                
    pipeline.ingestor.extract_pages_as_images = mocked_extract
    
    pdf_path = "510.pdf"
    if not os.path.exists(pdf_path):
        print(f"File {pdf_path} not found.")
        return
        
    print(f"Testing pipeline on the first 10 pages of {pdf_path}...")
    try:
        documents = pipeline.process_pdf(pdf_path)
        print("\n--- RESULTS ---")
        for doc in documents:
            print(f"Group: {doc.category.value} | Tenant: {doc.primary_tenant} | Pages: {doc.start_page}-{doc.end_page}")
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    test_first_10_pages()
