import pytest
from unittest.mock import MagicMock, patch
from src.llm import GemmaClient
import concurrent.futures

@patch("time.sleep")
def test_llm_api_exhaustion_raises_runtime_error(mock_sleep):
    client = GemmaClient("dummy_key")
    
    client.openrouter_client = None
    client.groq_client = None
    
    with patch("concurrent.futures.ThreadPoolExecutor.submit") as mock_submit:
        # We need to simulate the future raising an exception when result() is called, 
        # or the submit itself raising an exception.
        # Actually _route_llm_call catches Exception, so we can just have submit raise it.
        mock_submit.side_effect = Exception("Mocked API Error")
        
        with pytest.raises(RuntimeError, match="LLM routing failed across all providers"):
            client.classify_page_direct(b"dummy_data")
