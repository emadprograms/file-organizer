import time
import os
from src.pipeline import Pipeline
from src.llm import GemmaClient

# Dummy class to bypass actual API
class DummyClient:
    def __init__(self):
        self.calls = 0

    def classify_page(self, image_bytes):
        self.calls += 1
        print(f"DummyClient called {self.calls}")
        from src.llm import InvalidResponseError, LLMFailureError
        if self.calls < 3:
            raise InvalidResponseError("Simulated invalid response")
        return None

pipeline = Pipeline(api_keys=["dummy"])
pipeline.client = DummyClient()

def test_single_page():
    p_idx = 1
    i_bytes = b"dummy" * 5000
    res = None
    for attempt in range(3):
        try:
            print(f"Attempt {attempt}")
            res = pipeline.client.classify_page(image_bytes=i_bytes)
            break
        except Exception as e:
            if attempt < 2:
                print(f"Sleeping {2 ** attempt}")
                time.sleep(2 ** attempt)
            else:
                print(f"Fallback after 3 retries: {e}")
                res = "FALLBACK"
    print(res)

test_single_page()
