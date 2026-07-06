import pytest
from unittest.mock import MagicMock, patch
from src.llm.llm import LLMClient
from src.llm.providers import GeminiProvider, OpenRouterProvider, GroqProvider
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

import logging

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy', 'OPENROUTER_API_KEY': 'dummy', 'GROQ_API_KEY': 'dummy'})
@patch('src.llm.llm.time.sleep')
def test_llm_429_retry_and_failover(mock_sleep, caplog):
    caplog.set_level(logging.WARNING)
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
        
        warning_logs = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("429 error on gemini" in r.message.lower() for r in warning_logs), "Should warn about 429 error"

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy', 'OPENROUTER_API_KEY': 'dummy', 'GROQ_API_KEY': 'dummy'})
def test_llm_fallback_chain_on_5xx(caplog):
    caplog.set_level(logging.WARNING)
    client = LLMClient("dummy")
    with patch.object(GeminiProvider, 'generate') as mock_gemini, \
         patch.object(OpenRouterProvider, 'generate') as mock_openrouter, \
         patch.object(GroqProvider, 'generate') as mock_groq:
        
        mock_gemini.side_effect = Exception("500 Internal error")
        mock_openrouter.side_effect = Exception("500 Server error")
        mock_groq.return_value = DummyResponse(success=True)
        
        result = client._route_llm_call("model", ["test"], DummyResponse)
        
        assert result.success is True
        assert mock_gemini.call_count == 6
        mock_openrouter.assert_called_once()
        mock_groq.assert_called_once()
        
        warning_logs = [r.message.lower() for r in caplog.records if r.levelno == logging.WARNING]
        assert any("5xx/timeout on gemini" in msg for msg in warning_logs), "Should warn about 500 error"
        assert any("failed over to groq" in msg for msg in warning_logs), "Should warn about fallback to groq"

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy', 'OPENROUTER_API_KEY': 'dummy', 'GROQ_API_KEY': 'dummy'})
@patch('src.llm.llm.time.sleep')
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
            
        assert mock_gemini.call_count == 6
        mock_openrouter.assert_called_once()
        mock_groq.assert_called_once()




@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy'})
@patch('src.llm.llm.time.sleep')
def test_llm_500_max_retries_halts(mock_sleep, caplog):
    caplog.set_level(logging.WARNING)
    """
    Continuous 500 errors across all providers must halt with RuntimeError,
    not loop infinitely. Verifies max-retry limit is enforced.
    """
    client = LLMClient("dummy")
    with patch.object(GeminiProvider, 'generate') as mock_gemini, \
         patch.object(OpenRouterProvider, 'generate') as mock_openrouter, \
         patch.object(GroqProvider, 'generate') as mock_groq:

        # Every provider always returns a 500-class error
        mock_gemini.side_effect = Exception("500 Internal Server Error")
        mock_openrouter.side_effect = Exception("500 Internal Server Error")
        mock_groq.side_effect = Exception("500 Internal Server Error")

        with pytest.raises(RuntimeError, match="LLM routing failed across all providers"):
            client._route_llm_call("model", ["test"], DummyResponse)

        # Gemini must be called a finite number of times (≤ 6 as per retry logic)
        assert mock_gemini.call_count <= 6, (
            f"Expected at most 6 Gemini calls but got {mock_gemini.call_count} — "
            "retry loop may be infinite"
        )
        # At least 1 Gemini attempt must have been made
        assert mock_gemini.call_count >= 1

        # Sleep must be called (backoff happening)
        assert mock_sleep.call_count >= 1
        
        warning_logs = [r.message.lower() for r in caplog.records if r.levelno == logging.WARNING]
        assert any("5xx/timeout on gemini" in msg for msg in warning_logs), "Should warn about 500 error before halting"

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy'})
@patch('src.llm.llm.time.sleep')
def test_llm_trace_files_created(mock_sleep, tmp_path):
    from src.logger import LOGS_DIR
    import os
    import json
    
    # Overwrite LOGS_DIR for this test to avoid polluting actual logs
    with patch('src.logger.LOGS_DIR', str(tmp_path)):
        client = LLMClient("dummy")
        
        with patch.object(GeminiProvider, 'generate') as mock_gemini, \
             patch.object(OpenRouterProvider, 'generate') as mock_openrouter, \
             patch.object(GroqProvider, 'generate') as mock_groq:
            
            mock_openrouter.side_effect = Exception("OR Error")
            mock_groq.side_effect = Exception("Groq Error")
            
            # Test successful trace
            mock_gemini.return_value = DummyResponse(success=True)
            client._route_llm_call("model", ["test"], DummyResponse)
            
            traces_dir = tmp_path / "traces"
            assert traces_dir.exists()
            
            trace_files = list(traces_dir.glob("*.json"))
            assert len(trace_files) == 1
            assert not str(trace_files[0]).endswith(".error.json")
            
            # Test error trace
            mock_gemini.side_effect = Exception("Test Parse Error")
            with pytest.raises(Exception):
                client._route_llm_call("model", ["test"], DummyResponse)
                
            error_trace_files = list(traces_dir.glob("*.error.json"))
            assert len(error_trace_files) >= 3
