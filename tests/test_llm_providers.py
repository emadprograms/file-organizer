from typing import Any
import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel
from src.core.config import GEMINI_MODEL
from src.llm.providers import GeminiProvider
from google.genai import types
import base64

class PageClassification(BaseModel):
    category: str
    confidence: float

class DummyPart:
    def __init__(self, data, mime_type) -> Any:
        """
        Provide the   init   fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        self.data = data
        self.mime_type = mime_type

def test_gemini_provider_generate() -> None:
    """
    Test gemini provider generate.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    with patch('src.llm.providers.genai.Client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Mock response
        mock_response = MagicMock()
        mock_response.parsed = None
        mock_response.text = '```json\n{"category": "invoice", "confidence": 0.99}\n```'
        mock_instance.models.generate_content.return_value = mock_response

        provider = GeminiProvider("fake_key")
        
        # Construct content
        part = types.Part.from_bytes(data=b"dummy", mime_type="image/png")
        contents = ["test prompt", part]

        result = provider.generate(GEMINI_MODEL, contents, PageClassification)

        assert result.category == "invoice"
        assert result.confidence == 0.99
        
        # Verify call args
        mock_instance.models.generate_content.assert_called_once()
        call_args = mock_instance.models.generate_content.call_args[1]
        assert call_args["model"] == GEMINI_MODEL
        assert call_args["contents"] == contents
        assert call_args["config"].response_schema == PageClassification

def test_gemini_provider_error_handling() -> None:
    """
    Test gemini provider error handling.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    with patch('src.llm.providers.genai.Client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        mock_response = MagicMock()
        mock_response.parsed = None
        mock_response.text = 'invalid json output'
        mock_instance.models.generate_content.return_value = mock_response

        provider = GeminiProvider("fake_key")
        
        with pytest.raises(ValueError) as exc:
            provider.generate(GEMINI_MODEL, ["test"], PageClassification)
        
        assert "LLM parsing error" in str(exc.value)
        assert "invalid json output" in str(exc.value)

