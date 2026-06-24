import time
import os
import threading
from src.llm import GemmaClient

# Mock genai to simulate 429
class MockModels:
    def __init__(self):
        self.calls = 0
    def generate_content(self, *args, **kwargs):
        self.calls += 1
        print(f"Mocking API call {self.calls}...")
        raise Exception("429 Too Many Requests")

class MockClient:
    def __init__(self, api_key):
        self.models = MockModels()

import google.genai as genai
genai.Client = MockClient

os.environ["GEMINI_API_KEYS"] = "dummy_key1,dummy_key2"

client = GemmaClient(delay_between_pages=0)

# We will time how long it takes to fail, or if it spams endlessly.
start = time.time()
try:
    # Instead of letting it wait 65 seconds per attempt, we can mock time.sleep to see how many times it tries to sleep
    original_sleep = time.sleep
    sleeps = []
    def mock_sleep(s):
        print(f"Sleeping for {s} seconds")
        sleeps.append(s)
        # Don't actually sleep to keep test fast
    
    time.sleep = mock_sleep
    
    # Also patch pipeline retry
    for attempt in range(3):
        try:
            print(f"\n--- Pipeline Attempt {attempt} ---")
            client.classify_page(b"dummy")
            break
        except Exception as e:
            print(f"Caught {type(e).__name__}: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
finally:
    time.sleep = original_sleep
    print(f"\nTotal simulated time elapsed: {sum(sleeps)} seconds")
    print(f"Total API calls made: {sum(c.models.calls for c in client.clients.values())}")
