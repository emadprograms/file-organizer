import os
import sys
from unittest.mock import patch
from dotenv import load_dotenv

load_dotenv(".env")
from src.llm import GemmaClient

print("Initializing GemmaClient...")
client = GemmaClient(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))

# We want to simulate a 429 error on the very first try for Gemini.
# The code in src.llm checks:
# is_429 = "429" in error_str or "too many requests" in error_str or "quota" in error_str
# And if it is 429, it should sleep 65 seconds and retry.

# We will create a mock function that raises a 429 error on the first two calls,
# and then succeeds on the third call.
call_count = 0

def mock_generate_content(*args, **kwargs):
    global call_count
    call_count += 1
    if call_count <= 2:
        print(f"   [Mock] Simulating 429 Rate Limit error on attempt {call_count}...")
        raise Exception("429 Too Many Requests")
    else:
        print(f"   [Mock] Simulating successful response on attempt {call_count}...")
        # Return a mock response object that has a .parsed attribute
        class MockParsed:
            mapping_list = []
        class MockResponse:
            parsed = MockParsed()
            text = '{"mapping_list": []}'
        return MockResponse()

def mock_sleep(seconds):
    print(f"   [Mock time.sleep] Would have slept for {seconds} seconds!")

print("\nAttempting to cluster names with simulated 429 Rate Limit...")
with patch.object(client.client.models, 'generate_content', side_effect=mock_generate_content):
    with patch('time.sleep', side_effect=mock_sleep):
        try:
            result = client.cluster_names(["Mohamed"])
            print("\n✅ SUCCESS: LLM call eventually succeeded after handling the rate limit!")
        except Exception as e:
            print(f"\n❌ FAILED: {e}")
