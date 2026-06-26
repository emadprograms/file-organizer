import pytest
from unittest.mock import MagicMock, patch
from src.llm import GemmaClient
from src.schemas import PageClassification, Category

def test_fallback_when_needs_gemma_fallback_is_true():
    client = GemmaClient(api_keys=["dummy_key"])
    
    # Mock the local LLM response to return needs_gemma_fallback = True
    mock_local_response = PageClassification(
        house_number="UNKNOWN",
        residents=["NONE"],
        category=Category.OTHER_LETTERS,
        date="NONE",
        needs_gemma_fallback=True
    , summary="test")
    
    # Mock the gemini fallback route to return a successful classification
    mock_gemini_response = PageClassification(
        house_number="123",
        residents=["احمد"],
        category=Category.AMAR_TAKHSEES,
        date="2024-01-01",
        needs_gemma_fallback=False
    , summary="test")
    
    with patch.object(client, '_extract_text_with_qwen', return_value="dummy") as mock_extract:
        with patch.object(client, '_classify_text_with_local_model', return_value=mock_local_response) as mock_local:
            with patch.object(client, '_route_llm_call', return_value=mock_gemini_response) as mock_route:
                result = client.classify_page(b"dummy_image_bytes")
                
                # Assert local LLM was called
                mock_local.assert_called_once()
            
            # Assert _route_llm_call was called because needs_gemma_fallback was True
            mock_route.assert_called_once()
            assert mock_route.call_args[1]["model"] == "gemini-4-26b"
            
            # Assert the final result came from the fallback
            assert result.house_number == "123"
            assert result.category == Category.AMAR_TAKHSEES

def test_no_fallback_when_needs_gemma_fallback_is_false():
    client = GemmaClient(api_keys=["dummy_key"])
    
    # Mock the local LLM response to return needs_gemma_fallback = False
    mock_local_response = PageClassification(
        house_number="456",
        residents=["علي"],
        category=Category.MAINTENANCE,
        date="NONE",
        needs_gemma_fallback=False
    , summary="test")
    
    with patch.object(client, '_extract_text_with_qwen', return_value="dummy") as mock_extract:
        with patch.object(client, '_classify_text_with_local_model', return_value=mock_local_response) as mock_local:
            with patch.object(client, '_route_llm_call') as mock_route:
                result = client.classify_page(b"dummy_image_bytes")
                
                # Assert local LLM was called
                mock_local.assert_called_once()
            
            # Assert fallback was NOT called
            mock_route.assert_not_called()
            
            # Assert the final result came from the local LLM
            assert result.house_number == "456"
            assert result.category == Category.MAINTENANCE
