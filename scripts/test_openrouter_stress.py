import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup paths to import from src
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest import PdfIngestor
from src.llm import GemmaClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_openrouter_stress():
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

    pdf_file = "559.pdf"
    pdf_path = PROJECT_ROOT / "pdfs" / pdf_file
    
    if not pdf_path.exists():
        log.error(f"PDF not found at {pdf_path}")
        return

    log.info(f"Starting OpenRouter Stress Test using {pdf_file}")
    
    # Setup Clients
    # use_local_llm=False in GemmaClient tells it to use the Cloud (OpenRouter)
    client = GemmaClient(use_local_llm=False)
    ingestor = PdfIngestor()

    # Extract all pages as images
    log.info(f"Extracting pages from {pdf_file}...")
    pages = list(ingestor.extract_pages_as_images(str(pdf_path)))
    log.info(f"Extracted {len(pages)} pages.")

    request_count = 0
    start_time = time.time()

    try:
        for idx, img_bytes in pages:
            request_count += 1
            log.info(f"Processing Page {idx} (Request {request_count})...")
            
            try:
                # We use classify_page_direct which routes to the cloud model
                # Note: we set a high max_attempts in src/llm.py but we want to catch the 429 here.
                # In src/llm.py, _route_llm_call handles retries.
                # To truly test the rate limit and see it fail, we might want to bypass the 
                # internal retry loop or just let it exhaust.
                
                start_req = time.time()
                result = client.classify_page_direct(img_bytes)
                latency = time.time() - start_req
                log.info(f"Page {idx}: Success ({latency:.2f}s)")
                log.info(f"Result: {result}")
                
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "too many requests" in error_msg or "quota" in error_msg or "resource exhausted" in error_msg:
                    log.warning(f"!!! RATE LIMITED at Page {idx} (Request {request_count}) !!!")
                    log.warning(f"Error: {e}")
                    break
                else:
                    log.error(f"Page {idx}: Unexpected Error: {e}")
                    # Decide whether to continue or break. For rate limit testing, we usually break on 429.
                    # If it's a 500, we might just skip.
                    continue
            
            # User requested at least 3 seconds between requests
            time.sleep(3.0)

    except KeyboardInterrupt:
        log.info("Test interrupted by user.")

    end_time = time.time()
    duration = end_time - start_time
    log.info("="*40)
    log.info(f"Stress Test Completed.")
    log.info(f"Total successful requests before limit/end: {request_count if 'e' not in locals() else request_count-1}")
    log.info(f"Total duration: {duration:.2f}s")
    log.info("="*40)

if __name__ == "__main__":
    test_openrouter_stress()
