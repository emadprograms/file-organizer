import sys
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest import PdfIngestor
from src.llm import GemmaClient

PDF_PATH = PROJECT_ROOT / "508.pdf"

def run_hybrid_benchmark():
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    
    if not PDF_PATH.exists():
        print(f"Error: '{PDF_PATH}' not found.")
        sys.exit(1)
        
    print(f"Loading '{PDF_PATH}' for 50-page Hybrid Pipeline test...")
    ingestor = PdfIngestor()
    
    # We will grab exactly the first 50 pages
    page_images = []
    print("Extracting first 50 pages into memory...")
    extract_start = time.time()
    for page_idx, img_bytes in ingestor.extract_pages_as_images(str(PDF_PATH)):
        page_images.append((page_idx, img_bytes))
        if len(page_images) >= 50:
            break
    print(f"Extracted {len(page_images)} pages in {time.time() - extract_start:.2f}s")

    client = GemmaClient()
    
    # Clear state so we start fresh
    client.global_rpm_tracker.clear()
    client.global_cooldown_until = 0.0
    
    raw_pages = []
    deferred_local_pages = []
    
    print("\n==================================================")
    print("STARTING HYBRID PASS 1a (Cloud-First + Local Vision Fallback)")
    print("==================================================")
    start_time = time.time()
    
    for page_idx, img_bytes in page_images:
        print(f"\nProcessing Page {page_idx}...")
        
        if client.should_use_local_fallback():
            print("  [Rate Limit Active] Deferring to Local Vision OCR (qwen2.5vl:7b)...")
            try:
                text = client._extract_text_with_qwen(img_bytes)
                deferred_local_pages.append((page_idx, text))
                print(f"  -> Local OCR Complete (Text length: {len(text)})")
            except Exception as e:
                print(f"  -> Local OCR Failed: {e}")
        else:
            try:
                print("  [Cloud Ready] Calling Cloud Direct Classification (gemma-4-26b)...")
                result = client.classify_page_direct(img_bytes)
                raw_pages.append((page_idx, result))
                print(f"  -> Cloud Success: {result.category.value} | {result.residents}")
            except Exception as e:
                print(f"  -> Cloud Failed: {e}. Activating Cooldown and Falling back to Local OCR...")
                client.activate_cooldown()
                try:
                    text = client._extract_text_with_qwen(img_bytes)
                    deferred_local_pages.append((page_idx, text))
                    print(f"  -> Local OCR Complete (Text length: {len(text)})")
                except Exception as e2:
                    print(f"  -> Local OCR Failed: {e2}")
                    
    pass1a_time = time.time() - start_time
    print(f"\nPass 1a Complete in {pass1a_time:.2f}s. {len(raw_pages)} processed by Cloud, {len(deferred_local_pages)} deferred to Local Reasoning.")
    
    if deferred_local_pages:
        print("\n==================================================")
        print("STARTING HYBRID PASS 1b (Deferred Local Reasoning)")
        print("==================================================")
        pass1b_start = time.time()
        
        for page_idx, text in deferred_local_pages:
            print(f"Processing deferred Page {page_idx} with Local Reasoning (qwen2.5:14b)...")
            try:
                result = client._classify_text_with_local_model(text)
                raw_pages.append((page_idx, result))
                print(f"  -> Local Reasoning Success: {result.category.value} | {result.residents}")
            except Exception as e:
                print(f"  -> Local Reasoning Failed: {e}")
                
        pass1b_time = time.time() - pass1b_start
        print(f"Pass 1b Complete in {pass1b_time:.2f}s.")
    else:
        pass1b_time = 0.0
        
    total_time = time.time() - start_time
    
    print("\n================== BENCHMARK SUMMARY ==================")
    print(f"Total Pages Processed: {len(raw_pages)}")
    print(f"Pages Handled by Cloud: {len([p for p in raw_pages if p[0] not in [d[0] for d in deferred_local_pages]])}")
    print(f"Pages Handled by Local: {len(deferred_local_pages)}")
    print(f"Total Time: {total_time:.2f} seconds ({total_time/len(page_images):.2f}s per page avg)")
    print("=========================================================")

if __name__ == "__main__":
    run_hybrid_benchmark()
