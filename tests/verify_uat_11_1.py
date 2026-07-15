import pytest
from src.core.schemas import DocumentGroup
from src.routing.router import route_document
from src.llm.llm import LLMClient
from unittest.mock import MagicMock

def test_direct_routing_scenarios():
    # Mock LLMClient since direct routing should NOT use it
    mock_llm = MagicMock(spec=LLMClient)
    
    test_cases = [
        ("PERSONAL_DETAILS", "بيانات شخصية"),
        ("CONTRACT", "عقود"),
        ("EWA_LETTERS", "كهرباء وماء"),
        ("INSPECTION_PICTURES", "صور ومعاينات"),
    ]
    
    for category, expected_folder in test_cases:
        group = DocumentGroup(
            category=category,
            brief_arabic_title="Test Document",
            reason="Testing direct routing",
            start_page=1,
            end_page=1,
            primary_tenant="Test Tenant",
            dates=[]
        )
        
        folder, is_direct = route_document(group, mock_llm)
        
        print(f"Category: {category} -> Folder: {folder}, Direct: {is_direct}")
        
        assert folder == expected_folder, f"Expected {expected_folder}, got {folder} for {category}"
        assert is_direct is True, f"Expected direct routing for {category}"
        
    # Verify LLM was never called
    mock_llm.generate_content.assert_not_called()
    print("Verification successful: LLM was not called for direct routing.")

if __name__ == "__main__":
    test_direct_routing_scenarios()
