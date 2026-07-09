import pytest
from unittest.mock import MagicMock
from src.core.schemas import DocumentGroup
from src.processing.routing.router import route_document, RoutingResponse, RoutingValidationError

def test_route_document_single_match():
    # 'PERSONAL_DETAILS' is a SINGLE_MATCH (mapped only to 'بيانات شخصية')
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="PERSONAL_DETAILS", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    
    folder, is_direct = route_document(group, llm_client)
    
    assert folder == "بيانات شخصية"
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
    # 'BASIC_DETAILS' is currently a SINGLE_MATCH (mapped only to 'بيانات أساسية')
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="BASIC_DETAILS", dates=[], reason="R1", brief_arabic_title="Application"
    )
    llm_client = MagicMock()
    
    # Mock LLM to return a valid RoutingResponse
    mock_response = RoutingResponse.model_construct(selected_folder="بيانات أساسية", reason="Matches application form")
    llm_client.generate_content.return_value = mock_response
    
    folder, is_direct = route_document(group, llm_client)
    
    assert folder == "بيانات أساسية"
    assert is_direct is True
    # Note: since it's SINGLE_MATCH, llm_client.generate_content is NOT called.
    # If we wanted to test LLM, we'd need a category with multiple mappings.

def test_route_document_multi_match_invalid_folder():
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="OTHER_LETTERS", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    
    # LLM returns a folder NOT in the allowed list for 'OTHER_LETTERS'
    # In double_check_others, the allowed list is all folders.
    from pydantic import ValidationError
    llm_client.generate_content.side_effect = ValueError("Invalid folder")
    
    # double_check_others falls back to 'رسائل متنوعة' instead of raising RoutingValidationError
    folder, is_direct = route_document(group, llm_client)
    assert folder == "رسائل متنوعة"

def test_route_document_llm_failure_fallback():
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="OTHER_LETTERS", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    llm_client.generate_content.side_effect = Exception("API Error")
    
    # double_check_others falls back to 'رسائل متنوعة'
    folder, is_direct = route_document(group, llm_client)
    assert folder == "رسائل متنوعة"
