import os
import time
import logging
from google import genai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_gemini_rate_limit():
    api_keys_str = os.getenv("GEMINI_API_KEYS")
    if not api_keys_str:
        log.error("GEMINI_API_KEYS not found in environment")
        return
    
    keys = [k.strip() for k in api_keys_str.split(',')]
    key = keys[0]
    client = genai.Client(api_key=key)
    model_id = "gemini-2.0-flash" # Using flash for fast testing

    log.info(f"Testing Gemini rate limits with key: {key[:10]}...")
    
    request_count = 0
    start_time = time.time()
    
    try:
        while True:
            request_count += 1
            try:
                # Use a very simple prompt to minimize token usage and focus on RPM
                response = client.models.generate_content(
                    model=model_id,
                    contents="hi"
                )
                log.info(f"Request {request_count}: Success")
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "too many requests" in error_msg or "quota" in error_msg:
                    log.warning(f"Request {request_count}: RATE LIMITED! Error: {e}")
                    break
                else:
                    log.error(f"Request {request_count}: Unexpected Error: {e}")
                    break
            
            # Small delay to avoid instant burst if there's a very tight burst limit
            time.sleep(0.1)

    except KeyboardInterrupt:
        log.info("Testing interrupted by user.")

    end_time = time.time()
    duration = end_time - start_time
    log.info(f"Finished. Total successful requests: {request_count - 1}")
    log.info(f"Total time: {duration:.2f}s")
    log.info(f"Average requests per second: { (request_count-1)/duration:.2f}")

if __name__ == "__main__":
    test_gemini_rate_limit()
