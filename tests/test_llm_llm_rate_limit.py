from typing import Any
import pytest
from unittest.mock import MagicMock, patch
from src.llm.llm import LLMClient
from src.llm.providers import LLMProvider

class MockProvider(LLMProvider):
    def __init__(self, name="mock") -> Any:
        """
        Provide the   init   fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        self._name = name
        self.call_count = 0
        self.responses = []

    @property
    def name(self) -> str:
        return self._name

    def generate(self, model, contents, response_schema=None, validation_context=None) -> Any:
        """
        Provide the generate fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        self.call_count += 1
        if self.call_count <= len(self.responses):
            resp = self.responses[self.call_count - 1]
            if isinstance(resp, Exception):
                raise resp
            return resp
        return "Success"

def test_rate_limit_retry() -> None:
    """
    Test rate limit retry.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    rate_limit_error = Exception("API Error: 429 Too Many Requests")
    mock_provider = MockProvider(name="gemini")
    mock_provider.responses = [rate_limit_error, "Success"]
    
    client = LLMClient(api_key="fake_key")
    client.provider = mock_provider
    
    with patch("time.sleep") as mock_sleep:
        result = client.generate_content("Hello", model="test-model")
        
        assert result == "Success"
        assert mock_provider.call_count == 2
        from unittest.mock import call
        assert call(65) in mock_sleep.mock_calls
