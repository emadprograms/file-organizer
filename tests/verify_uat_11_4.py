import pytest
from unittest.mock import MagicMock, patch
from src.core.schemas import DocumentGroup
from src.processing.routing.router import route_document
from src.llm.llm import LLMClient
from pydantic import BaseModel

class MockRoutingResponse(BaseModel):
    selected_folder: str
    reason: str

def test_escape_hatch_none_of_the_above():
    # Setup Mock LLM
    mock_llm = MagicMock(spec=LLMClient)
    
    # We need to simulate multiple calls to generate_content:
    # 1st call: Initial routing -> returns "None of the above"
    # 2nd call: double_check_others Step 1 -> returns "رسائل متنوعة"
    mock_llm.generate_content.side_effect = [
        MockRoutingResponse(selected_folder="None of the above", reason="Does not fit the specific categories"),
        MockRoutingResponse(selected_folder="رسائل متنوعة", reason="Confirmed miscellaneous")
    ]
    
    group = DocumentGroup(
        category="MODIFICATIONS",
        brief_arabic_title="Random Document",
        reason="Does not fit standard folders",
        start_page=1,
        end_page=1,
        primary_tenant="Test Tenant",
        dates=[]
    )
    
    # We patch SINGLE_MATCH so MODIFICATIONS goes through the LLM routing
    with patch('src.processing.routing.router.SINGLE_MATCH', set()):
        folder, is_direct = route_document(group, mock_llm)
    
    print(f"Category: MODIFICATIONS -> Folder: {folder}, Direct: {is_direct}")
    
    # Verify folder
    assert folder == "رسائل متنوعة"
    assert is_direct is False
    
    # Verify generate_content was called twice
    assert mock_llm.generate_content.call_count == 2
    
    # Verify the first call prompt contained "None of the above"
    call_args_list = mock_llm.generate_content.call_args_list
    first_call_kwargs = call_args_list[0][1]
    first_prompt = first_call_kwargs['contents'][0]
    assert "None of the above" in first_prompt
    
    # Verify the second call prompt was the double check prompt
    second_call_kwargs = call_args_list[1][1]
    second_prompt = second_call_kwargs['contents'][0]
    assert "re-evaluate if it fits into any of the following specific folders" in second_prompt
    
    print("Verification successful: Escape hatch correctly triggered 'Others' flow.")

if __name__ == "__main__":
    test_escape_hatch_none_of_the_above()
