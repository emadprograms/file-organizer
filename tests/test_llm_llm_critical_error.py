from typing import Any
import pytest
from unittest.mock import MagicMock, patch
from src.llm.llm import LLMClient, LLMFailureError
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

def test_critical_error_halt() -> None:
    """
    Test critical error halt.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    auth_error = Exception("API Error: 401 Unauthorized - Invalid API Key")
    mock_provider = MockProvider(name="gemini")
    mock_provider.responses = [auth_error, "Success"]
    
    client = LLMClient(api_key="fake_key")
    client.provider = mock_provider
    
    with pytest.raises(LLMFailureError, match="Critical LLM API error"):
        client.generate_content("Hello", model="test-model")
        
    assert mock_provider.call_count == 1
