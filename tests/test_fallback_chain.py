import pytest
from unittest.mock import patch, MagicMock
from src.llm import GemmaClient, LLMFailureError
from src.schemas import Category, PageClassification

@pytest.fixture
def gemma_client():
    with patch.dict('os.environ', {'GEMINI_API_KEY': 'gemini_key', 'OPENROUTER_API_KEY': 'or_key', 'GROQ_API_KEY': 'groq_key'}):
        return GemmaClient(api_key="gemini_key")

class MockParsed:
    def __init__(self):
        self.category = Category.BASIC_DETAILS
        self.house_number = "123"
        self.residents = ["Ahmed"]
        self.date = "2020-01-01"
        self.summary = "Test"

class MockGeminiResponse:
    def __init__(self):
        self.parsed = MockParsed()

class MockOpenAIResponse:
    def __init__(self, content):
        self.choices = [MagicMock()]
        self.choices[0].message.content = content

@patch('time.sleep')
def test_route_gemini_success(mock_sleep, gemma_client):
    with patch.object(gemma_client.client.models, 'generate_content', return_value=MockGeminiResponse()) as mock_gemini:
        res = gemma_client._route_llm_call("model", ["test"], PageClassification)
        assert res.category == Category.BASIC_DETAILS
        mock_gemini.assert_called_once()
        mock_sleep.assert_called() # Sleeps for the remainder of 7s rate limit

@patch('time.sleep')
def test_route_fallback_to_openrouter_on_429(mock_sleep, gemma_client):
    """Gemini 429 fails 3 times, falls back to OpenRouter"""
    with patch.object(gemma_client.client.models, 'generate_content', side_effect=Exception("429 Too Many Requests")) as mock_gemini:
        with patch.object(gemma_client.openrouter_client.chat.completions, 'create', return_value=MockOpenAIResponse('{"category": "Basic Details Form", "house_number": "123", "residents": ["Ahmed"], "date": "2020-01-01", "summary": "Test", "is_form": true}')) as mock_or:
            res = gemma_client._route_llm_call("model", ["test"], PageClassification)
            
            assert mock_gemini.call_count == 3
            mock_or.assert_called_once()
            assert res.house_number == "123"

@patch('time.sleep')
def test_route_fallback_immediately_on_500(mock_sleep, gemma_client):
    """Gemini 500 fails once, immediately falls back to OpenRouter"""
    with patch.object(gemma_client.client.models, 'generate_content', side_effect=Exception("500 Internal Server Error")) as mock_gemini:
        with patch.object(gemma_client.openrouter_client.chat.completions, 'create', return_value=MockOpenAIResponse('{"category": "Basic Details Form", "house_number": "123", "residents": ["Ahmed"], "date": "2020-01-01", "summary": "Test", "is_form": true}')) as mock_or:
            res = gemma_client._route_llm_call("model", ["test"], PageClassification)
            
            assert mock_gemini.call_count == 1
            mock_or.assert_called_once()
            assert res.house_number == "123"

@patch('time.sleep')
def test_route_fails_fast_on_auth_error(mock_sleep, gemma_client):
    """Gemini 401 fails immediately without retrying or falling back"""
    with patch.object(gemma_client.client.models, 'generate_content', side_effect=Exception("401 Unauthorized")) as mock_gemini:
        with pytest.raises(LLMFailureError):
            gemma_client._route_llm_call("model", ["test"], PageClassification)
        assert mock_gemini.call_count == 1
