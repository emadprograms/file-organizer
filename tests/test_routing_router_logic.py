from typing import Any
import pytest
from unittest.mock import MagicMock
from src.core.schemas import DocumentGroup
from src.routing.router import route_document, RoutingResponse, RoutingValidationError

import pytest
from unittest.mock import MagicMock
from src.core.schemas import DocumentGroup
from src.routing.router import route_document, RoutingResponse, RoutingValidationError

def test_route_document_single_match() -> None:
    """
    Test route document single match.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    # 'id_cards' is mapped directly to 'بيانات شخصية'
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="id_cards", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    
    folder, is_direct = route_document(group, llm_client)
    
    assert folder == "بيانات شخصية"
    assert is_direct is True
    llm_client.generate_content.assert_not_called()

def test_route_document_no_mapping() -> None:
    """
    Test route document no mapping.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    # 'unknown_cat' falls back to 'forms' and will try LLM. We mock LLM to fail.
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="unknown_cat", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    llm_client.generate_content.side_effect = Exception("API Error")
    
    with pytest.raises(RoutingValidationError):
        route_document(group, llm_client)

from unittest.mock import patch

@patch('src.routing.router.SINGLE_MATCH', set())
def test_route_document_multi_match_success() -> None:
    """
    Test route document multi match success.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    # 'BASIC_DETAILS' requires LLM to route when not in SINGLE_MATCH
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
    assert is_direct is False
    assert llm_client.generate_content.called

def test_route_document_multi_match_invalid_folder() -> None:
    """
    Test route document multi match invalid folder.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="others", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    
    # LLM returns a ValueError on double_check_others
    llm_client.generate_content.side_effect = ValueError("Invalid folder")
    
    # double_check_others falls back to 'رسائل متنوعة' instead of raising RoutingValidationError
    folder, is_direct = route_document(group, llm_client)
    assert folder == "رسائل متنوعة"

def test_route_document_llm_failure_fallback() -> None:
    """
    Test route document llm failure fallback.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="T1", 
        category="others", dates=[], reason="R1"
    )
    llm_client = MagicMock()
    llm_client.generate_content.side_effect = Exception("API Error")
    
    # double_check_others falls back to 'رسائل متنوعة'
    folder, is_direct = route_document(group, llm_client)
    assert folder == "رسائل متنوعة"
