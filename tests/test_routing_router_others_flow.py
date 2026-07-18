from typing import Any
import pytest
from unittest.mock import MagicMock, patch
from src.core.schemas import DocumentGroup
from src.routing.router import route_document
from src.llm.llm import LLMClient
from pydantic import BaseModel

class MockRoutingResponse(BaseModel):
    selected_folder: str
    reason: str

def get_base_group() -> Any:
    """
    Provide the get base group fixture/mock.

    Returns:
    The appropriate fixture or mock value.
    """
    return DocumentGroup(
        category="OTHER_LETTERS", # This category immediately triggers double_check_others
        brief_arabic_title="Misc Document",
        reason="Needs sorting",
        start_page=1,
        end_page=1,
        primary_tenant="Test Tenant",
        dates=[]
    )

def test_uat_11_5_immediate_misc() -> None:
    """
    Test uat 11 5 immediate misc.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    mock_llm = MagicMock(spec=LLMClient)
    # Step 1: LLM picks "رسائل متنوعة" directly
    mock_llm.generate_content.return_value = MockRoutingResponse(
        selected_folder="رسائل متنوعة", 
        reason="It is just misc"
    )
    
    group = get_base_group()
    folder, is_direct = route_document(group, mock_llm)
    
    assert folder == "رسائل متنوعة"
    assert is_direct is False
    assert mock_llm.generate_content.call_count == 1

def test_uat_11_6_confirmed_match() -> None:
    """
    Test uat 11 6 confirmed match.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    mock_llm = MagicMock(spec=LLMClient)
    # Step 1: LLM picks "صيانة"
    # Step 2: LLM confirms "صيانة"
    mock_llm.generate_content.side_effect = [
        MockRoutingResponse(selected_folder="صيانة", reason="Looks like maintenance"),
        MockRoutingResponse(selected_folder="صيانة", reason="Yes, it is maintenance")
    ]
    
    group = get_base_group()
    folder, is_direct = route_document(group, mock_llm)
    
    assert folder == "صيانة"
    assert is_direct is False
    assert mock_llm.generate_content.call_count == 2

def test_uat_11_7_confirmation_change() -> None:
    """
    Test uat 11 7 confirmation change.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    mock_llm = MagicMock(spec=LLMClient)
    # Step 1: LLM picks "صيانة"
    # Step 2: LLM changes mind to "رسائل متنوعة"
    mock_llm.generate_content.side_effect = [
        MockRoutingResponse(selected_folder="صيانة", reason="Looks like maintenance"),
        MockRoutingResponse(selected_folder="رسائل متنوعة", reason="Actually, it's just a general letter")
    ]
    
    group = get_base_group()
    folder, is_direct = route_document(group, mock_llm)
    
    assert folder == "رسائل متنوعة"
    assert is_direct is False
    assert mock_llm.generate_content.call_count == 2

def test_uat_11_8_hallucination_fallback() -> None:
    """
    Test uat 11 8 hallucination fallback.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    mock_llm = MagicMock(spec=LLMClient)
    # Step 1: LLM picks "صيانة"
    # Step 2: LLM returns an invalid folder not in the allowed list during confirmation
    mock_llm.generate_content.side_effect = [
        MockRoutingResponse(selected_folder="صيانة", reason="Looks like maintenance"),
        ValueError("Selected folder 'Invalid Folder' is not in the allowed list")
    ]
    
    group = get_base_group()
    folder, is_direct = route_document(group, mock_llm)
    
    # It should catch the error and fallback to "رسائل متنوعة"
    assert folder == "رسائل متنوعة"
    assert is_direct is False
    assert mock_llm.generate_content.call_count == 2

if __name__ == "__main__":
    test_uat_11_5_immediate_misc()
    test_uat_11_6_confirmed_match()
    test_uat_11_7_confirmation_change()
    test_uat_11_8_hallucination_fallback()
    print("All tests passed.")
