import pytest
import logging
from unittest.mock import MagicMock, patch
from src.llm.llm import LLMClient
from src.llm.providers import GeminiProvider
from pydantic import BaseModel

logger = logging.getLogger(f"file_organizer.{__name__}")

class DummyResponse(BaseModel):
    success: bool

@patch.dict('os.environ', {'GEMINI_API_KEY': 'dummy'})
def test_llm_trace_files_created(tmp_path):
    from src.llm.llm import LLMClient
    
    # We verify that the LLMClient calls the trace logging function with correct data
    with patch('src.llm.llm.log_decision_trace') as mock_trace:
        client = LLMClient("dummy")
        
        with patch.object(GeminiProvider, 'generate') as mock_gemini:
            
            # Test successful trace
            mock_gemini.return_value = DummyResponse(success=True)
            client._route_llm_call("model", ["test"], DummyResponse)
            
            # Verify success trace was called
            mock_trace.assert_any_call("llm_success", {
                "model": "model",
                "provider": "gemini",
                "prompt": ["test"],
                "response": {"success": True}
            })
            
            # Test error trace
            mock_gemini.side_effect = Exception("Test Parse Error")
            with pytest.raises(Exception):
                client._route_llm_call("model", ["test"], DummyResponse)
            
            # Verify error trace was called
            mock_trace.assert_any_call("llm_error", {
                "error": "Test Parse Error",
                "model": "model",
                "provider": "gemini",
                "prompt": ["test"]
            })
