import pytest
import os
from unittest.mock import patch, MagicMock
from src.core.config import GEMINI_MODEL
from src.llm.llm import LLMClient
from src.llm.providers import GeminiProvider, OpenRouterProvider, GroqProvider
import logging

@patch.dict('os.environ', {
    'OPENROUTER_API_KEY': 'invalid_or_key',
    'GROQ_API_KEY': 'invalid_groq_key'
})
def test_live_fallback_invalid_key_fail_fast(caplog):
    caplog.set_level(logging.WARNING)
    client = LLMClient(api_key="invalid_gemini_key")
    
    with patch.object(OpenRouterProvider, 'generate') as mock_or, \
         patch.object(GroqProvider, 'generate') as mock_groq:
        
        # We will directly call _route_llm_call to verify it raises,
        # because cluster_names swallows the exception.
        from src.core.schemas import EntityResolutionMapping
        with pytest.raises(Exception) as excinfo:
            client._route_llm_call(
                model=GEMINI_MODEL,
                contents=["test"],
                response_schema=EntityResolutionMapping
            )
            
        error_msg = str(excinfo.value).lower()
        assert "400" in error_msg or "api key not valid" in error_msg or "invalid_api_key" in error_msg or "403" in error_msg
        
        # Ensure secondary providers were NOT invoked
        mock_or.assert_not_called()
        mock_groq.assert_not_called()
        
        # Verify that warning was logged
        warning_logs = [record for record in caplog.records if record.levelno == logging.WARNING]
        assert any("Auth/Bad Request error" in record.message for record in warning_logs), "Should log warning on auth fail"

def test_mocked_fallback_chain_integration(caplog):
    caplog.set_level(logging.WARNING)
    client = LLMClient(api_key="dummy")
    # Need to force providers to exist if not loaded by environ
    client.providers = [
        GeminiProvider("dummy"),
        OpenRouterProvider("dummy"),
        GroqProvider("dummy")
    ]
    
    with patch.object(GeminiProvider, 'generate') as mock_gemini, \
         patch.object(OpenRouterProvider, 'generate') as mock_openrouter, \
         patch.object(GroqProvider, 'generate') as mock_groq:
        
        mock_gemini.side_effect = Exception("503 Service Unavailable")
        mock_openrouter.side_effect = Exception("500 Internal Error")
        
        # Groq returns a valid string since we switched to text mode
        mock_groq.return_value = "DIFFERENT -> TEST"
        
        # other_names must not match anchor_names phonetically so it reaches the LLM tier
        result = client.cluster_names(["TEST"], ["DIFFERENT"], "dummy template")
        # If it falls back correctly to Groq, cluster_names will succeed and return mapping
        assert result == {"DIFFERENT": "TEST"}
        
        # Ensure providers were called expected number of times
        assert mock_gemini.call_count == 6
        mock_openrouter.assert_called_once()
        mock_groq.assert_called_once()
        
        # Verify fallback warnings were logged
        warning_logs = [record for record in caplog.records if record.levelno == logging.WARNING]
        assert any("5xx/timeout on gemini" in record.message.lower() for record in warning_logs), "Should warn about gemini 5xx"
        assert any("cloud fallback" in record.message.lower() for record in warning_logs), "Should log cloud fallback"
