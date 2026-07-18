from typing import Any
import pytest
from src.core.schemas import DocumentGroup
from src.routing.router import route_document
from src.llm.llm import LLMClient
from unittest.mock import MagicMock
from pydantic import BaseModel

class MockRoutingResponse(BaseModel):
    selected_folder: str
    reason: str

def test_constrained_routing_forms() -> None:
    """
    Test constrained routing forms.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    # Setup Mock LLM
    mock_llm = MagicMock(spec=LLMClient)
    
    # Scenario 1: Correct routing within constraints
    # We mock the return value of generate_content
    mock_llm.generate_content.return_value = MockRoutingResponse(
        selected_folder="صيانة", 
        reason="Document is about house repairs"
    )
    
    group = DocumentGroup(
        category="FORMS",
        brief_arabic_title="Maintenance Request",
        reason="Request for fixing a leak",
        start_page=1,
        end_page=1,
        primary_tenant="Test Tenant",
        dates=[]
    )
    
    from unittest.mock import patch
    with patch('src.routing.router.SINGLE_MATCH', set()):
        folder, is_direct = route_document(group, mock_llm)
    
    print(f"Category: MAINTENANCE -> Folder: {folder}, Direct: {is_direct}")
    
    # Verify folder
    assert folder == "صيانة"
    assert is_direct is False
    
    # Verify the prompt contained the constrained list
    # The arguments to generate_content are passed as kwargs
    args, kwargs = mock_llm.generate_content.call_args
    prompt = kwargs['contents'][0] # First content item is usually the formatted prompt
    
    # Form folders: {"بيانات أساسية", "محضر تسليم مفتاح", "صيانة", "تعديلات", "رسائل متنوعة"}
    # Plus "None of the above"
    assert "صيانة" in prompt
    assert "بيانات أساسية" in prompt
    assert "None of the above" in prompt
    # Should NOT contain a letter-only folder
    assert "أمر تخصيص" not in prompt
    
    print("Verification successful: Constraints were correctly applied to the prompt.")

def test_constrained_routing_validation_failure() -> None:
    """
    Test constrained routing validation failure.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    # Setup Mock LLM to return an invalid folder (outside the constrained list)
    mock_llm = MagicMock(spec=LLMClient)
    
    # Mock first call to return invalid folder, second call to return valid one
    # Note: route_document uses a loop for retries. 
    # The actual validation happens in the Pydantic model RoutingResponse inside route_document
    # But route_document's `generate_content` is called and then the result is used.
    # Wait, the validation is inside the `RoutingResponse` Pydantic model using `validation_context`.
    # In a real run, Pydantic would raise ValidationError if the LLM returned something not in allowed_folders.
    
    # Since we are mocking the return value, we need to simulate the ValidationError 
    # that the actual `llm_client.generate_content` would raise when it tries to instantiate RoutingResponse.
    from pydantic import ValidationError
    
    # Mock first call to raise ValueError, second call to return valid
    mock_llm.generate_content.side_effect = [
        ValueError("Selected folder 'Invalid Folder' is not in the allowed list: []"),
        MockRoutingResponse(selected_folder="صيانة", reason="Fixed on second try")
    ]
    
    group = DocumentGroup(
        category="FORMS",
        brief_arabic_title="Maintenance Request",
        reason="Request for fixing a leak",
        start_page=1,
        end_page=1,
        primary_tenant="Test Tenant",
        dates=[]
    )
    
    from unittest.mock import patch
    with patch('src.routing.router.SINGLE_MATCH', set()):
        folder, is_direct = route_document(group, mock_llm)
    
    assert folder == "صيانة"
    assert mock_llm.generate_content.call_count == 2
    print("Verification successful: Validation failure triggered a retry.")

if __name__ == "__main__":
    test_constrained_routing_forms()
    test_constrained_routing_validation_failure()
