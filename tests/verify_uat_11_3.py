import pytest
from unittest.mock import MagicMock, patch
from src.core.schemas import DocumentGroup
from src.processing.routing.router import route_document
from src.llm.llm import LLMClient
from pydantic import BaseModel

class MockRoutingResponse(BaseModel):
    selected_folder: str
    reason: str

def test_constrained_routing_letters():
    # Setup Mock LLM
    mock_llm = MagicMock(spec=LLMClient)
    
    # Scenario 1: Correct routing within constraints
    # We mock the return value of generate_content
    mock_llm.generate_content.return_value = MockRoutingResponse(
        selected_folder="إشعارات", 
        reason="Document is a warning notification"
    )
    
    group = DocumentGroup(
        category="NOTIFICATIONS",
        brief_arabic_title="Warning Notice",
        reason="Warning for unpaid bills",
        start_page=1,
        end_page=1,
        primary_tenant="Test Tenant",
        dates=[]
    )
    
    with patch('src.processing.routing.router.SINGLE_MATCH', set()):
        folder, is_direct = route_document(group, mock_llm)
    
    print(f"Category: NOTIFICATIONS -> Folder: {folder}, Direct: {is_direct}")
    
    # Verify folder
    assert folder == "إشعارات"
    assert is_direct is False
    
    # Verify the prompt contained the constrained list
    # The arguments to generate_content are passed as kwargs
    args, kwargs = mock_llm.generate_content.call_args
    prompt = kwargs['contents'][0] # First content item is usually the formatted prompt
    
    # Letter folders: {"أمر تخصيص", "استقطاع إيجار", "وقف استقطاع بدل", "إشعارات", "كهرباء وماء", "رسائل متنوعة"}
    # Plus "None of the above"
    assert "إشعارات" in prompt
    assert "أمر تخصيص" in prompt
    assert "None of the above" in prompt
    # Should NOT contain a form-only folder like "محضر تسليم مفتاح"
    assert "محضر تسليم مفتاح" not in prompt
    
    print("Verification successful: Letter constraints were correctly applied to the prompt.")

if __name__ == "__main__":
    test_constrained_routing_letters()
