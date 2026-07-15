import pytest
from unittest.mock import MagicMock, patch, call
from src.llm.llm import LLMClient, LLMFailureError
from src.llm.providers import LLMProvider
from src.core.exceptions import ProviderRotationExhaustedError

class MockProvider(LLMProvider):
    def __init__(self, name, behavior=None):
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
    class HTTPError(Exception):
        def __str__(self):
            return f"HTTP Error {status_code}: Some error message"
    return HTTPError(status_code)

@pytest.fixture
def llm_client():
    with patch('src.llm.llm.os.getenv', side_effect=lambda *args, **kwargs: args[0] == "GEMINI_API_KEY" and "fake_key" or ""):
        client = LLMClient(api_key="fake_key")
        client.provider = MockProvider("gemini")
        return client

def test_resilience_429_retry_limit(llm_client):
    llm_client.provider.behavior = [raise_http_error(429)] * 10
    
    with patch('time.sleep') as mock_sleep:
        with pytest.raises(ProviderRotationExhaustedError):
            llm_client._route_llm_call(model="test-model", contents=["test"])
        mock_sleep.assert_has_calls([call(65), call(65), call(65)], any_order=False)
        assert mock_sleep.call_count == 3

def test_resilience_401_immediate_halt(llm_client):
    llm_client.provider.behavior = [raise_http_error(401)] * 10
    with patch('time.sleep') as mock_sleep:
        with pytest.raises(LLMFailureError):
            llm_client._route_llm_call(model="test-model", contents=["test"])
        mock_sleep.assert_not_called()
