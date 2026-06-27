import os
import sys
import time
import base64
import logging
from pathlib import Path
from dotenv import load_dotenv
import openai

# Setup paths to import from src
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest import PdfIngestor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_openrouter_direct_stress():
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        log.error("OPENROUTER_API_KEY not found in environment")
        return

    pdf_file = "559.pdf"
    pdf_path = PROJECT_ROOT / "pdfs" / pdf_file
    if not pdf_path.exists():
        log.error(f"PDF not found at {pdf_path}")
        return

    model_id = "google/gemma-4-26b-a4b-it:free"
    
    # Direct OpenAI client for OpenRouter
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    log.info(f"Starting DIRECT OpenRouter Stress Test using {pdf_file}")
    log.info(f"Model: {model_id}")
    
    ingestor = PdfIngestor()
    log.info(f"Extracting pages from {pdf_file}...")
    pages = list(ingestor.extract_pages_as_images(str(pdf_path)))
    log.info(f"Extracted {len(pages)} pages.")

    request_count = 0
    start_time = time.time()

    try:
        for idx, img_bytes in pages:
            request_count += 1
            log.info(f"Processing Page {idx} (Request {request_count})...")
            
            # Convert image bytes to base64
            base64_image = base64.b64encode(img_bytes).decode('utf-8')
            
            try:
                start_req = time.time()
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Classify this document page. Return JSON only."},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ]
                )
                latency = time.time() - start_req
                log.info(f"Page {idx}: Success ({latency:.2f}s)")
                log.info(f"Response: {response.choices[0].message.content[:200]}...")
                
            except Exception as e:
                error_msg = str(e).lower()
                # Catching rate limit errors specifically
                if "429" in error_msg or "too many requests" in error_msg or "quota" in error_msg:
                    log.warning(f"!!! RATE LIMITED by OpenRouter at Page {idx} (Request {request_count}) !!!")
                    log.warning(f"Error: {e}")
                    break
                else:
                    log.error(f"Page {idx}: Unexpected Error: {e}")
                    continue
            
            # Maintain the 3-second delay requested by the user
            time.sleep(3.0)

    except KeyboardInterrupt:
        log.info("Test interrupted by user.")

    end_time = time.time()
    duration = end_time - start_time
    log.info("="*40)
    log.info(f"Direct Stress Test Completed.")
    log.info(f"Total successful requests before limit/end: {request_count if 'e' not in locals() else request_count-1}")
    log.info(f"Total duration: {duration:.2f}s")
    log.info("="*40)

if __name__ == "__main__":
    test_openrouter_direct_stress()
