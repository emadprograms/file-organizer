import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

from src.pipeline import Pipeline

def main():
    pdf_path = "1273.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        sys.exit(1)
        
    print(f"Initializing pipeline...")
    pipeline = Pipeline(delay_between_pages=0) # delay 0 for max throughput
    
    print(f"Starting processing of {pdf_path}...")
    try:
        docs = pipeline.process_pdf(pdf_path)
        print(f"\nSUCCESS! Processed into {len(docs)} document groups.")
        
        import dataclasses
        out_path = "1273_output.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([dataclasses.asdict(doc) for doc in docs], f, ensure_ascii=False, indent=2)
        print(f"Output saved to {out_path}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nFAILED with {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
