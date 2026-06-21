import os
from dotenv import load_dotenv
from src.pipeline import Pipeline
from src.split import extract_pdf_segment

def main():
    load_dotenv()
    
    api_keys_str = os.getenv("GEMINI_API_KEYS")
    api_keys = [k.strip() for k in api_keys_str.split(",")] if api_keys_str else None
    
    pipeline = Pipeline(api_keys=api_keys)
    
    sample_pdf = "sample.pdf"
    if not os.path.exists(sample_pdf):
        print(f"Please provide a {sample_pdf} in the root directory to run.")
        return
        
    documents = pipeline.process_pdf(sample_pdf)
    print(f"Identified {len(documents)} documents.")
    
    for doc in documents:
        start = doc["start_page"]
        end = doc["end_page"]
        category = doc["data"].get("category", "Unknown")
        name = doc["data"].get("resident_name", "Unknown")
        
        out_filename = f"out_{start}-{end}_{category}_{name}.pdf".replace("/", "_").replace(" ", "_")
        print(f"Extracting pages {start}-{end} to {out_filename}")
        extract_pdf_segment(sample_pdf, start, end, out_filename)

if __name__ == "__main__":
    main()
