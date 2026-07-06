import pytest
import time
from unittest.mock import patch, MagicMock
from src.llm_client import (
    LLMClient,
    LLMClientError,
    LLMChunkShrinkRequiredError,
    LLMRateLimitError,
    LLMServerError,
)
from google.genai.errors import APIError

@pytest.fixture
def mock_sleep():
    with patch("src.llm_client.time.sleep") as mock:
        yield mock

@pytest.fixture
def llm_client():
    with patch("src.llm_client.genai.Client") as MockClient:
        client = LLMClient(api_key="fake_key")
        # Give a mock response
        mock_response = MagicMock()
        mock_response.text = "mocked"
        client.client.models.generate_content.return_value = mock_response
        yield client

def test_success_call(llm_client, mock_sleep):
    with patch("src.llm_client.time.time", side_effect=[1000.0, 1010.0]):
        response = llm_client.generate_content("test")
        assert response.text == "mocked"
        mock_sleep.assert_not_called()

def test_rate_limit_enforced(llm_client, mock_sleep):
    # Mock time.time so elapsed is 2s (1002 - 1000), should sleep 5s (7 - 2)
    with patch("src.llm_client.time.time", side_effect=[1000.0, 1000.0, 1002.0, 1002.0, 1010.0]):
        llm_client.generate_content("test1")
        llm_client.generate_content("test2")
        mock_sleep.assert_called_with(5.0)

def test_400_fails_fast(llm_client, mock_sleep):
    error = APIError("Bad Request", {})
    error.code = 400
    llm_client.client.models.generate_content.side_effect = error
    
    with pytest.raises(LLMClientError, match="HTTP 400"):
        llm_client.generate_content("test")

def test_429_retry_and_fail(llm_client, mock_sleep):
    error = APIError("Rate Limit", {})
    error.code = 429
    llm_client.client.models.generate_content.side_effect = error
    
    with patch("src.llm_client.time.time", return_value=1000.0):
        with pytest.raises(LLMRateLimitError):
            llm_client.generate_content("test")
            
    sleeps = [call[0][0] for call in mock_sleep.call_args_list]
    assert sleeps.count(65) == 2

def test_500_retry_success(llm_client, mock_sleep):
    error = APIError("Server Error", {})
    error.code = 500
    
    # 2 failures, then success
    mock_resp = MagicMock()
    mock_resp.text = "success"
    llm_client.client.models.generate_content.side_effect = [error, error, mock_resp]
    
    with patch("src.llm_client.time.time", return_value=1000.0):
        resp = llm_client.generate_content("test")
        assert resp.text == "success"
        sleeps = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleeps.count(15) == 2

def test_500_boundary_call_shrink_and_fail(llm_client, mock_sleep):
    error = APIError("Server Error", {})
    error.code = 500
    llm_client.client.models.generate_content.side_effect = error
    
    with patch("src.llm_client.time.time", return_value=1000.0):
        with pytest.raises(LLMChunkShrinkRequiredError, match="Boundary call failed"):
            llm_client.generate_content("test", is_boundary_call=True)
            
    sleeps = [call[0][0] for call in mock_sleep.call_args_list]
    assert sleeps.count(15) == 4

def test_500_non_boundary_skip(llm_client, mock_sleep):
    error = APIError("Server Error", {})
    error.code = 500
    llm_client.client.models.generate_content.side_effect = error
    
    with patch("src.llm_client.time.time", return_value=1000.0):
        resp = llm_client.generate_content("test", is_boundary_call=False)
        assert resp is None
        sleeps = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleeps.count(15) == 4

def test_404_fails_fast(llm_client, mock_sleep):
    error = APIError("Not Found", {})
    error.code = 404
    llm_client.client.models.generate_content.side_effect = error
    
    with pytest.raises(LLMClientError, match="HTTP 404"):
        llm_client.generate_content("test")
