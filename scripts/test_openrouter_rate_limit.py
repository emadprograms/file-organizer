import os
import time
import logging
import openai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_openrouter_rate_limit():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        log.error("OPENROUTER_API_KEY not found in environment")
        return
    
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    model_id = "google/gemma-4-26b-a4b-it:free"

    log.info(f"Testing OpenRouter rate limits with model: {model_id}...")
    
    request_count = 0
    start_time = time.time()
    
    try:
        while True:
            request_count += 1
            try:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": "hi"}]
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
            
            # Small delay to avoid instant burst
            time.sleep(3.0)

    except KeyboardInterrupt:
        log.info("Testing interrupted by user.")

    end_time = time.time()
    duration = end_time - start_time
    log.info(f"Finished. Total successful requests: {request_count - 1}")
    log.info(f"Total time: {duration:.2f}s")
    log.info(f"Average requests per second: { (request_count-1)/duration:.2f}")

if __name__ == "__main__":
    test_openrouter_rate_limit()
