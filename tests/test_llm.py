import pytest
from unittest.mock import MagicMock, patch
from src.llm import LLMClient
from src.providers import GeminiProvider, OpenRouterProvider, GroqProvider
from pydantic import BaseModel

class DummyResponse(BaseModel):
    success: bool

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy', 'OPENROUTER_API_KEY': 'dummy', 'GROQ_API_KEY': 'dummy'})
def test_llm_auth_error_fails_fast():
    client = LLMClient("dummy")
    with patch.object(GeminiProvider, 'generate') as mock_gemini:
        mock_gemini.side_effect = Exception("401 Unauthorized")
        
        with pytest.raises(Exception, match="401"):
            client._route_llm_call("model", ["test"], DummyResponse)
            
        mock_gemini.assert_called_once()

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy', 'OPENROUTER_API_KEY': 'dummy', 'GROQ_API_KEY': 'dummy'})
@patch('src.llm.time.sleep')
def test_llm_429_retry_and_failover(mock_sleep):
    client = LLMClient("dummy")
    with patch.object(GeminiProvider, 'generate') as mock_gemini, \
         patch.object(OpenRouterProvider, 'generate') as mock_openrouter:
        
        mock_gemini.side_effect = Exception("429 Too many requests")
        mock_openrouter.return_value = DummyResponse(success=True)
        
        result = client._route_llm_call("model", ["test"], DummyResponse)
        
        assert result.success is True
        assert mock_gemini.call_count == 3
        assert mock_openrouter.call_count == 1
        assert mock_sleep.call_count >= 2

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy', 'OPENROUTER_API_KEY': 'dummy', 'GROQ_API_KEY': 'dummy'})
def test_llm_fallback_chain_on_5xx():
    client = LLMClient("dummy")
    with patch.object(GeminiProvider, 'generate') as mock_gemini, \
         patch.object(OpenRouterProvider, 'generate') as mock_openrouter, \
         patch.object(GroqProvider, 'generate') as mock_groq:
        
        mock_gemini.side_effect = Exception("500 Internal error")
        mock_openrouter.side_effect = Exception("500 Server error")
        mock_groq.return_value = DummyResponse(success=True)
        
        result = client._route_llm_call("model", ["test"], DummyResponse)
        
        assert result.success is True
        assert mock_gemini.call_count == 2
        mock_openrouter.assert_called_once()
        mock_groq.assert_called_once()

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy', 'OPENROUTER_API_KEY': 'dummy', 'GROQ_API_KEY': 'dummy'})
@patch('src.llm.time.sleep')
def test_llm_exhaustion(mock_sleep):
    client = LLMClient("dummy")
    with patch.object(GeminiProvider, 'generate') as mock_gemini, \
         patch.object(OpenRouterProvider, 'generate') as mock_openrouter, \
         patch.object(GroqProvider, 'generate') as mock_groq:
        
        mock_gemini.side_effect = Exception("500 Internal error")
        mock_openrouter.side_effect = Exception("500 Server error")
        mock_groq.side_effect = Exception("500 Server error")
        
        with pytest.raises(RuntimeError, match="LLM routing failed across all providers"):
            client._route_llm_call("model", ["test"], DummyResponse)
            
        assert mock_gemini.call_count == 2
        mock_openrouter.assert_called_once()
        mock_groq.assert_called_once()
