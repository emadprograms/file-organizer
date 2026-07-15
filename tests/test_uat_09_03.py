import pytest
from unittest.mock import MagicMock, patch
from src.llm.llm import LLMClient, LLMFailureError
from src.llm.providers import LLMProvider

class MockProvider:
    def __init__(self, name="mock"):
        self._name = name
        self.call_count = 0
        self.responses = []

    @property
    def name(self) -> str:
        return self._name

    def generate(self, model, contents, response_schema=None, validation_context=None):
        self.call_count += 1
        if self.call_count <= len(self.responses):
            resp = self.responses[self.call_count - 1]
            if isinstance(resp, Exception):
                raise resp
            return resp
        return "Success"

def test_routing_failure_isolation():
    print("Testing UAT-09-03: Routing failure isolation")
    
    # We want to simulate a scenario where:
    # 1. First call fails with a non-critical error (e.g., 500)
    # 2. Second call succeeds
    # 3. Verify that the failure in the first didn't "lock out" or permanently break the client.
    
    server_error = Exception("API Error: 500 Internal Server Error")
    mock_provider = MockProvider(name="gemini")
    mock_provider.responses = [server_error, "Success"]
    
    client = LLMClient(api_key="fake_key")
    client.provider = mock_provider
    
    with patch("time.sleep"):
        # First call: should fail after retries or rotate provider
        # Since we only have one provider, it will retry 3 times then fail with LLMFailureError
        try:
            client.generate_content("First call (fail)", model="test-model")
        except LLMFailureError:
            print("First call failed as expected.")
        
        # Second call: should succeed
        # We need to make sure the mock provider is still working.
        # However, our current MockProvider uses call_count. 
        # To simulate a second *independent* request succeeding, we can reset responses.
        mock_provider.responses = ["Success"]
        mock_provider.call_count = 0
        
        result = client.generate_content("Second call (success)", model="test-model")
        assert result == "Success"
        print("Second call succeeded. Isolation verified.")

    print("UAT-09-03 PASS")

if __name__ == "__main__":
    try:
        test_routing_failure_isolation()
        print("VERIFICATION PASSED")
    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
