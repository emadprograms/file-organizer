import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel
from src.config import GEMINI_MODEL
from src.providers import GeminiProvider, OpenRouterProvider, GroqProvider
from google.genai import types
import base64

class PageClassification(BaseModel):
    category: str
    confidence: float

class DummyPart:
    def __init__(self, data, mime_type):
        self.data = data
        self.mime_type = mime_type

def test_gemini_provider_generate():
    with patch('src.providers.genai.Client') as mock_client:
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

def test_openrouter_provider_generate():
    with patch('src.providers.openai.Client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '```\n{"category": "receipt", "confidence": 0.8}\n```'
        mock_instance.chat.completions.create.return_value = mock_response

        provider = OpenRouterProvider("fake_key")
        
        part = DummyPart(b"dummy", "image/png")
        contents = ["test prompt", part]

        result = provider.generate("mock_model", contents, PageClassification)
        
        assert result.category == "receipt"
        assert result.confidence == 0.8
        
        mock_instance.chat.completions.create.assert_called_once()
        call_args = mock_instance.chat.completions.create.call_args[1]
        messages = call_args["messages"]
        assert messages[0]["role"] == "user"
        content = messages[0]["content"]
        assert content[0] == {"type": "text", "text": "test prompt"}
        assert content[1] == {"type": "image_url", "image_url": {"url": "data:image/png;base64,ZHVtbXk="}}

def test_groq_provider_generate():
    with patch('src.providers.openai.Client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"category": "other", "confidence": 0.5}'
        mock_instance.chat.completions.create.return_value = mock_response

        provider = GroqProvider("fake_key")
        
        part = DummyPart(b"dummy", "image/jpeg")
        contents = ["test prompt groq", part]

        result = provider.generate("mock_model", contents, PageClassification)
        
        assert result.category == "other"
        assert result.confidence == 0.5
        
        mock_instance.chat.completions.create.assert_called_once()
        call_args = mock_instance.chat.completions.create.call_args[1]
        messages = call_args["messages"]
        assert messages[0]["role"] == "user"
        content = messages[0]["content"]
        assert content[0] == {"type": "text", "text": "test prompt groq"}
        assert content[1] == {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,ZHVtbXk="}}

def test_gemini_provider_error_handling():
    with patch('src.providers.genai.Client') as mock_client:
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

def test_openrouter_provider_error_handling():
    with patch('src.providers.openai.Client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'bad text'
        mock_instance.chat.completions.create.return_value = mock_response

        provider = OpenRouterProvider("fake_key")
        
        with pytest.raises(ValueError) as exc:
            provider.generate("mock_model", ["test"], PageClassification)
        
        assert "LLM parsing error" in str(exc.value)
        assert "bad text" in str(exc.value)
