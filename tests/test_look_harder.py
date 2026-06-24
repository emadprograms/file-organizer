import time
import logging
from unittest.mock import patch, MagicMock
from src.llm import GemmaClient
from src.schemas import PageClassification, Category

logging.basicConfig(level=logging.INFO)

def run_test():
    client = GemmaClient(api_keys=["dummy_key"])
    
    call_counter = {"count": 0}
    
    def mock_generate_content(*args, **kwargs):
        call_counter["count"] += 1
        print(f"--- API Call {call_counter['count']} triggered ---")
        
        if call_counter["count"] == 1:
            print("Simulating first call returning NO residents (NONE)...")
            mock_resp = MagicMock()
            mock_resp.parsed = PageClassification(
                category=Category.BASIC_DETAILS,
                residents=["NONE"],
                date="NONE",
                house_number="123"
            )
            return mock_resp
        else:
            print("Simulating 'look harder' retry hitting a 429 Rate Limit...")
            raise Exception("429 Too Many Requests")

    original_sleep = time.sleep
    def fast_sleep(seconds):
        original_sleep(0.01)

    with patch('google.genai.Client') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.models.generate_content.side_effect = mock_generate_content
        for k in client.clients:
            client.clients[k] = mock_instance
            
        with patch('time.sleep', side_effect=fast_sleep):
            try:
                res = client.classify_page(b"dummy")
                print("\nFinal Result from classify_page:")
                print(f"Residents: {res.residents}")
            except Exception as e:
                print(f"\nCaught exception: {e}")

if __name__ == "__main__":
    run_test()
