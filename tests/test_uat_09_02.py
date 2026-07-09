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
        print(f"MockProvider.generate called. call_count={self.call_count}, responses_len={len(self.responses)}")
        if self.call_count <= len(self.responses):
            resp = self.responses[self.call_count - 1]
            print(f"Returning/Raising response: {resp}")
            if isinstance(resp, Exception):
                raise resp
            return resp
        print("No more responses, returning Success")
        return "Success"

def test_critical_error_halt():
    print("Testing UAT-09-02: Critical error halt (401/403/400)")
    
    auth_error = Exception("API Error: 401 Unauthorized")
    mock_provider = MockProvider(name="gemini")
    mock_provider.responses = [auth_error]
    
    client = LLMClient(api_key="fake_key")
    client.providers = [mock_provider]
    
    try:
        print("Calling generate_content...")
        result = client.generate_content("Hello", model="test-model")
        print(f"Call returned without exception: {result}")
    except LLMFailureError as e:
        print(f"Caught expected LLMFailureError: {e}")
        assert "Critical LLM API error" in str(e)
        assert mock_provider.call_count == 1
        print("UAT-09-02 PASS")
        return
    except Exception as e:
        print(f"Caught unexpected exception {type(e).__name__}: {e}")
        raise e

    print("FAILED: LLMFailureError was not raised")
    exit(1)

if __name__ == "__main__":
    try:
        test_critical_error_halt()
        print("VERIFICATION PASSED")
    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
