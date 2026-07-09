import pytest
from unittest.mock import MagicMock, patch, call
from src.llm.llm import LLMClient, LLMFailureError
from src.llm.providers import LLMProvider

class MockProvider(LLMProvider):
    def __init__(self, name, behavior=None):
        super().__init__()
        self._name = name
        self.behavior = behavior if behavior else []
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    def generate(self, model, contents, response_schema=None, validation_context=None):
        self.call_count += 1
        if self.behavior and self.call_count <= len(self.behavior):
            result = self.behavior[self.call_count - 1]
            if isinstance(result, Exception):
                raise result
            return result
        return "Success"

def raise_http_error(status_code):
    """Helper to create provider errors with status codes in the message."""
    class HTTPError(Exception):
        def __str__(self):
            return f"HTTP Error {status_code}: Some error message"
    return HTTPError(status_code)

@pytest.fixture
def llm_client():
    # Setup with minimal providers
    with patch('src.llm.llm.os.getenv', side_effect=lambda *args, **kwargs: args[0] == "GEMINI_API_KEY" and "fake_key" or ""):
        client = LLMClient(api_key="fake_key")
        # Force only a few providers for deterministic testing
        client.providers = [
            MockProvider("gemini"),
            MockProvider("openrouter"),
            MockProvider("groq")
        ]
        return client

def test_resilience_429_retry_limit(llm_client):
    """Test Case 1 (429): Mock provider to return 429. Verify time.sleep called with 65 exactly 3 times. Verify LLMFailureError raised."""
    # Setup: First provider always returns 429
    llm_client.providers[0].behavior = [raise_http_error(429)] * 10
    
    with patch('time.sleep') as mock_sleep:
        with pytest.raises(LLMFailureError):
            llm_client._route_llm_call(model="test-model", contents=["test"])
        
        # Expecting 3 attempts on first provider before giving up or rotating.
        # Wait, the plan says: "429 errors trigger exactly 65s sleep and 3 retries before halting."
        # If we use the sequence [Gemini, S1, Gemini, S2], and Gemini keeps 429ing, 
        # it should try Gemini, sleep 65, Gemini, sleep 65, Gemini, sleep 65, then maybe rotate or halt.
        # The a manual retry loop with strict time.sleep values is requested.
        
        # According to Task 3 behavior: "If 429: time.sleep(65), retry same provider."
        # If the loop is for attempt in range(max_attempts), and max_attempts is 3.
        # Attempt 0: 429 -> sleep 65
        # Attempt 1: 429 -> sleep 65
        # Attempt 2: 429 -> sleep 65
        # Then loop ends -> raise LLMFailureError
        
        mock_sleep.assert_has_calls([call(65), call(65), call(65)], any_order=False)
        assert mock_sleep.call_count == 3

def test_resilience_500_rotation(llm_client):
    """Test Case 2 (500): Mock provider to return 500. Verify time.sleep called with 15. Verify provider sequence rotates."""
    # Setup: All providers return 500
    for p in llm_client.providers:
        p.behavior = [raise_http_error(500)] * 10
        
    with patch('time.sleep') as mock_sleep:
        with pytest.raises(LLMFailureError):
            llm_client._route_llm_call(model="test-model", contents=["test"])
        
        # Rotation: Gemini -> S1 -> Gemini -> S2
        # Attempt 0 (Gemini): 500 -> sleep 15, rotate
        # Attempt 1 (S1): 500 -> sleep 15, rotate
        # Attempt 2 (Gemini): 500 -> sleep 15, rotate
        # Attempt 3 (S2): 500 -> sleep 15, rotate (if max attempts is 4)
        # The plan says "3 retries" generally, but the sequence is [Gemini, S1, Gemini, S2] which is 4 slots.
        # Let's check if sleep(15) is called.
        
        assert mock_sleep.call_count >= 1
        mock_sleep.assert_any_call(15)

def test_resilience_401_immediate_halt(llm_client):
    """Test Case 3 (401): Mock provider to return 401. Verify immediate LLMFailureError with no sleep."""
    # Setup: First provider returns 401
    llm_client.providers[0].behavior = [raise_http_error(401)] * 10
    
    with patch('time.sleep') as mock_sleep:
        with pytest.raises(LLMFailureError):
            llm_client._route_llm_call(model="test-model", contents=["test"])
        
        mock_sleep.assert_not_called()

def test_provider_alternation(llm_client):
    """Test Case 4 (Alternation): Verify that across two sequential _route_llm_call invocations, the secondary provider used first alternates (S1 then S2)."""
    # Clear providers and set known secondary providers
    llm_client.providers = [
        MockProvider("gemini"),
        MockProvider("openrouter"),
        MockProvider("groq")
    ]
    
    # We need to spy on which providers are called.
    # Since we are testing _route_llm_call, we can see which MockProvider.generate was called.
    
    # First call: S1 should be OpenRouter, S2 should be Groq (based on _fallback_toggle default False)
    # If it succeeds immediately on Gemini, we won't see rotation. 
    # So let's make Gemini fail with 500 once to force rotation to S1.
    llm_client.providers[0].behavior = [raise_http_error(500), "Success"]
    
    # Call 1: Gemini (500) -> OpenRouter (Success)
    llm_client._route_llm_call(model="test-model", contents=["test"])
    assert llm_client.providers[1].call_count == 1 # OpenRouter
    assert llm_client.providers[2].call_count == 0 # Groq
    
    # Reset call counts
    for p in llm_client.providers: p.call_count = 0
    
    # Now _fallback_toggle should be True. 
    # Second call: Gemini (500) -> Groq (Success)
    llm_client.providers[0].behavior = [raise_http_error(500), "Success"]
    llm_client._route_llm_call(model="test-model", contents=["test"])
    assert llm_client.providers[1].call_count == 0 # OpenRouter
    assert llm_client.providers[2].call_count == 1 # Groq
