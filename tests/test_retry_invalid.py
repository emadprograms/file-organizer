import time
import logging
from unittest.mock import patch, MagicMock
from src.pipeline import Pipeline
from src.llm import GemmaClient, InvalidResponseError, LLMFailureError

logging.basicConfig(level=logging.INFO)

def run_test():
    pipeline = Pipeline(api_keys=["dummy_key"])
    
    call_counter = {"count": 0}
    
    def mock_classify_page(*args, **kwargs):
        call_counter["count"] += 1
        print(f"--- API Call {call_counter['count']} triggered ---")
        
        if call_counter["count"] == 1:
            print("Simulating LLM returning invalid JSON (InvalidResponseError)...")
            raise InvalidResponseError("Simulated Invalid JSON Response")
        else:
            print("Simulating Google API 429 Too Many Requests inside classify_page (LLMFailureError)...")
            # If classify_page hits 429 and exhausts retries, it raises LLMFailureError
            raise LLMFailureError("Simulated 429 Rate Limit Exhaustion")

    # Mock time.sleep and time.time so we don't actually wait 65 seconds
    original_sleep = time.sleep
    current_time = [time.time()]
    def fast_sleep(seconds):
        print(f"[MOCK SLEEP] Sleeping for {seconds:.1f}s")
        current_time[0] += seconds
        
    def mock_time():
        return current_time[0]

    with patch.object(pipeline.client, 'classify_page', side_effect=mock_classify_page):
        with patch('src.ingest.PdfIngestor.extract_pages_as_images', return_value=[(1, b"dummy_bytes")]):
            with patch('time.sleep', side_effect=fast_sleep):
                with patch('time.time', side_effect=mock_time):
                    try:
                        res = pipeline.process_pdf("dummy.pdf")
                        print("\nTest completed. Pipeline successfully recovered using fallback.")
                    except Exception as e:
                        print(f"\nCaught fatal exception in test: {e}")

if __name__ == "__main__":
    run_test()
