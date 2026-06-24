import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.pipeline import Pipeline
from src.organizer import FileOrganizer

def main():
    load_dotenv(dotenv_path=".env")
    
    api_keys_str = os.getenv("GEMINI_API_KEYS")
    api_keys = [k.strip() for k in api_keys_str.split(",")] if api_keys_str else []
            
    if not api_keys:
        print("No API keys found!")
        return

    folder = 'C:/Users/Emad/Documents/Safra C'
    files_to_process = []
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.lower().endswith('.pdf'):
                path = os.path.join(folder, f)
                size_kb = os.path.getsize(path) / 1024
                if size_kb < 10500:
                    files_to_process.append(path)
                    
    files_to_process.sort(key=lambda x: os.path.getsize(x))
    
    target_files = ["1264.pdf", "1358.pdf", "528.pdf", "1340.pdf"]
    files_to_process = [os.path.join(folder, f) for f in target_files if os.path.exists(os.path.join(folder, f))]
    
    print(f"Targeting specific {len(files_to_process)} files.")
    
    pipeline = Pipeline(api_keys=api_keys, delay_between_pages=0.5)
    organizer = FileOrganizer()
    
    for idx, pdf_path in enumerate(files_to_process, 1):
        print(f"\n==================================================")
        print(f"[{idx}/{len(files_to_process)}] Processing: {pdf_path}")
        print(f"==================================================")
        try:
            documents = pipeline.process_pdf(pdf_path)
            out_dir = Path(folder)
            summary = organizer.organize(documents, pdf_path, out_dir)
            if summary:
                print(f"Successfully organized {len(summary)} PDFs for {os.path.basename(pdf_path)}!")
        except Exception as e:
            print(f"Failed on {pdf_path}: {e}")

if __name__ == "__main__":
    main()
