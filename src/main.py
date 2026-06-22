import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from src.pipeline import Pipeline
from src.organizer import FileOrganizer
import sys

def main():
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Process and categorize housing documents.")
    parser.add_argument("pdf_path", help="Path to the input PDF file")
    parser.add_argument("-o", "--output", default="./output", help="Base output directory")
    args = parser.parse_args()
    
    api_keys_str = os.getenv("GEMINI_API_KEYS")
    api_keys = [k.strip() for k in api_keys_str.split(",")] if api_keys_str else None
    
    pipeline = Pipeline(api_keys=api_keys)
    
    if not os.path.exists(args.pdf_path):
        print(f"Please provide a valid PDF file at {args.pdf_path} to run.")
        return
        
    documents = pipeline.process_pdf(args.pdf_path)
    print(f"Identified {len(documents)} documents.")
    
    organizer = FileOrganizer()
    summary = organizer.organize(documents, args.pdf_path, Path(args.output))
    
    if summary:
        house_number = organizer._resolve_house_number(documents)
        num_residents = len(organizer._build_resident_order(documents))
        output_dir = Path(args.output) / house_number
        
        print(f"\n{'='*50}")
        print(f"  House: {house_number}")
        print(f"  Residents: {num_residents}")
        print(f"  PDFs generated: {len(summary)}")
        print(f"  Output: {output_dir}")
        print(f"{'='*50}")

if __name__ == "__main__":
    main()
