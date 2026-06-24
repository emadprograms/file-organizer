import os
import sys

from src.pipeline import Pipeline

def main():
    pdf_path = "1250.pdf"
    if not os.path.exists(pdf_path):
        print(f"{pdf_path} not found!")
        sys.exit(1)
        
    print(f"Initializing pipeline...")
    pipeline = Pipeline()
    
    print(f"Starting processing of {pdf_path}...")
    try:
        docs = pipeline.process_pdf(pdf_path)
        print(f"Processed {len(docs)} documents.")
    except Exception as e:
        print(f"Pipeline crashed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
