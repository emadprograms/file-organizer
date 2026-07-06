import pytest
import logging
from unittest.mock import MagicMock, patch
from src.llm.llm import LLMClient
from src.core.schemas import GroupingResponse, GroupEntry
from src.processing.routing import RoutingResponse

def test_llm_client_skip_llm_grouping():
    """Verify that skip_llm returns a mocked GroupingResponse with parsed bounds."""
    client = LLMClient("dummy_key")
    client.skip_llm = True
    
    # Mock a prompt that looks like what the pipeline sends
    contents = ["Chunk range: Page 5 to Page 10"]
    response_schema = GroupingResponse
    
    result = client._route_llm_call("model", contents, response_schema)
    
    assert isinstance(result, GroupingResponse)
    assert len(result.groups) == 1
    assert result.groups[0].start_page == 5
    assert result.groups[0].end_page == 10
    assert result.groups[0].reason == "mock skip-llm"

def test_llm_client_skip_llm_routing():
    """Verify that skip_llm returns a mocked RoutingResponse."""
    client = LLMClient("dummy_key")
    client.skip_llm = True
    
    contents = ["some routing prompt"]
    response_schema = RoutingResponse
    
    result = client._route_llm_call("model", contents, response_schema)
    
    assert isinstance(result, RoutingResponse)
    assert result.selected_folder == "13_others"

def test_llm_client_skip_llm_plain_text():
    """Verify that skip_llm returns a mock string when no schema is provided."""
    client = LLMClient("dummy_key")
    client.skip_llm = True
    
    contents = ["some prompt"]
    result = client._route_llm_call("model", contents, None)
    
    assert result == "mock plain text response"
def test_llm_client_verbose_logging(caplog):
    """Verify that verbose=True triggers debug logging of prompt and response."""
    caplog.set_level(logging.DEBUG)
    client = LLMClient("dummy_key")
    client.verbose = True

    # Mock the first provider's generate method to avoid network calls
    with patch.object(client.providers[0], 'generate', return_value="mock response"):
        client._route_llm_call("model", ["test prompt"], None)

        assert "Prompt: ['test prompt']" in caplog.text
        assert "Response: mock response" in caplog.text

def test_llm_client_non_verbose_logging(caplog):
    """Verify that verbose=False does NOT trigger debug logging of prompt and response."""
    caplog.set_level(logging.DEBUG)
    client = LLMClient("dummy_key")
    client.verbose = False

    # Mock the first provider's generate method to avoid network calls
    with patch.object(client.providers[0], 'generate', return_value="mock response"):
        client._route_llm_call("model", ["test prompt"], None)

        assert "Prompt: ['test prompt']" not in caplog.text
        assert "Response: mock response" not in caplog.text
