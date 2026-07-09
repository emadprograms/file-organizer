import pytest
from unittest.mock import MagicMock
from src.core.schemas import DocumentGroup
from src.processing.routing.router import route_document, RoutingResponse, RoutingValidationError

def test_route_document_single_match():
    # 'id_cards' is a SINGLE_MATCH (mapped only to '2_personal_details')
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="id_cards", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    
    folder, is_direct = route_document(group, llm_client)
    
    assert folder == "2_personal_details"
    assert is_direct is True
    llm_client.generate_content.assert_not_called()

def test_route_document_no_mapping():
    # 'unknown_cat' is not in CATEGORY_TO_FOLDERS
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="unknown_cat", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    
    with pytest.raises(RoutingValidationError):
        route_document(group, llm_client)

def test_route_document_multi_match_success():
    # 'forms' can be routed to multiple folders
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="forms", dates=[], reason="R1", brief_arabic_title="Application"
    )
    llm_client = MagicMock()
    
    # Mock LLM to return a valid RoutingResponse
    mock_response = RoutingResponse.model_construct(selected_folder="1_requests_and_applications", reason="Matches application form")
    llm_client.generate_content.return_value = mock_response
    
    folder, is_direct = route_document(group, llm_client)
    
    assert folder == "1_requests_and_applications"
    assert is_direct is False
    llm_client.generate_content.assert_called_once()

def test_route_document_multi_match_invalid_folder():
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="forms", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    
    # LLM returns a folder NOT in the allowed list for 'forms'
    from pydantic import ValidationError
    llm_client.generate_content.side_effect = ValueError("Invalid folder")
    
    with pytest.raises(RoutingValidationError):
        route_document(group, llm_client)

def test_route_document_llm_failure_fallback():
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="forms", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    llm_client.generate_content.side_effect = Exception("API Error")
    
    with pytest.raises(RoutingValidationError):
        route_document(group, llm_client)
