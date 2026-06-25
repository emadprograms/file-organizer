import pytest
from unittest.mock import patch, MagicMock
from src.llm import GemmaClient, PageClassification
import base64

def test_prompt_contains_conflict_resolution_rules():
    """
    Test that the system prompt explicitly contains the disambiguation 
    rules to prevent category conflicts. This prevents future regressions.
    """
    # Mock the API keys so we don't need real ones just to instantiate the client
    with patch("os.getenv", return_value="dummy_key"):
        client = GemmaClient(api_keys=["dummy_key"])
        prompt = client._build_system_prompt()

    # 1. Rent vs Allowance Conflict
    assert "30 bd" in prompt.lower() or "60 bd" in prompt.lower(), "Missing rent vs allowance BD amounts rule."
    assert "disambiguate from allowance" in prompt.lower() or "وقف استقطاع بدل الانتفاع" in prompt, "Missing allowance context."

    # 2. Amar Takhsees Strictness Conflict
    assert "higher authority" in prompt.lower() or "someone important" in prompt.lower(), "Missing Amar Takhsees strict definition."
    assert "do not classify random documents" in prompt.lower(), "Missing false positive penalty for Amar Takhsees."

    # 3. Eviction Notices Conflict
    assert "home eviction" in prompt.lower() or "eviction" in prompt.lower(), "Missing eviction notice classification rule."
    assert "not in other_letters" in prompt.lower() or "not in other letters" in prompt.lower(), "Missing exclusion of eviction from other_letters."

    # 4. Basic Details vs Personal Details vs Rent Deduction Form
    assert "form" in prompt.lower(), "Missing form dependency for basic_details."
    assert "never basic_details" in prompt.lower() and ("30" in prompt or "60" in prompt), "Missing 30/60 financial amount exclusion from basic_details."
    assert "family" in prompt.lower(), "Missing family inclusion for personal_details."
    
    # 5. Maintenance / Inspection / Ashgal Conflict
    assert "inspection" in prompt.lower(), "Missing 'inspection' keyword routing for maintenance."
    assert "الأشغال" in prompt, "Missing Ashgal keyword routing for maintenance."
    assert "temporary key handovers" in prompt.lower() or "never key_handover_form" in prompt.lower(), "Missing Ashgal exclusion from key handover."


@patch("src.llm.GemmaClient._route_llm_call")
def test_fallback_routing_on_conflict(mock_route):
    """
    Test that if the local model hits a conflict and cannot find a subject/strong pattern,
    the fallback flag properly routes to Gemma 26b instead of failing.
    """
    with patch("os.getenv", return_value="dummy_key"):
        client = GemmaClient(api_keys=["dummy_key"])
        
    # Mock the local LLM response to simulate a conflict/confusion
    mock_local_response = MagicMock()
    mock_local_response.choices = [MagicMock()]
    mock_parsed = MagicMock()
    mock_parsed.needs_gemma_fallback = True
    mock_local_response.choices[0].message.parsed = mock_parsed

    # Set up the fallback expected response
    expected_fallback_result = PageClassification(
        house_number="123",
        residents=["محمد علي"],
        category="amar_takhsees",
        date="2020-01-01",
        needs_gemma_fallback=False
    )
    mock_route.return_value = expected_fallback_result

    with patch.object(client.local_client.beta.chat.completions, 'parse', return_value=mock_local_response):
        # We pass a dummy image
        result = client.classify_page(b"dummy_image_bytes")
        
        # Verify the fallback was triggered because of the conflict flag
        assert mock_route.called, "Gemma fallback was not called when local LLM flagged a conflict."
        assert result.category == "amar_takhsees"
