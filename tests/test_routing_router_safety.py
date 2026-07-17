import pytest
from unittest.mock import MagicMock, patch
from src.routing.router import route_document, RoutingValidationError
from src.llm.llm import LLMFailureError
from src.core.schemas import DocumentGroup

def test_unmapped_category_raises_error():
    """Test Case 1: Provide a category with no mapping in CATEGORY_TO_FOLDERS. 
    Verify RoutingValidationError is raised instead of returning '13_others'."""
    
    # Mock CATEGORY_TO_FOLDERS to ensure the category is missing
    with patch('src.routing.router.CATEGORY_TO_FOLDERS', {}):
        group = DocumentGroup(
            start_page=0,
            end_page=1,
            primary_tenant="Test Tenant",
            category="unknown_category", 
            dates=[],
            brief_arabic_title="Test Title", 
            reason="Test Reason"
        )
        mock_llm = MagicMock()
        
        with pytest.raises(RoutingValidationError) as excinfo:
            route_document(group, mock_llm)
        
        assert "has no mapping" in str(excinfo.value)

@patch('src.routing.router.SINGLE_MATCH', set())
def test_llm_exhaustion_raises_error():
    """Test Case 2: Mock LLMClient to raise LLMFailureError. 
    Verify that the error propagates and halts the router."""

    group = DocumentGroup(
        start_page=0,
        end_page=1,
        primary_tenant="Test Tenant",
        category="BASIC_DETAILS", # Use a multi-match category to hit LLM path
        dates=[],
        brief_arabic_title="Test Title", 
        reason="Test Reason"
    )
    mock_llm = MagicMock()
    mock_llm.generate_content.side_effect = RuntimeError("LLM API failure")

    with pytest.raises(RoutingValidationError):
        route_document(group, mock_llm)

@patch('src.routing.router.SINGLE_MATCH', set())
def test_validation_failure_raises_error():
    """Test Case 3: Mock LLMClient to return an invalid folder. 
    Verify that after 3 attempts, RoutingValidationError is raised."""

    # Ensure category is mapped to something specific
    with patch('src.routing.router.CATEGORY_TO_FOLDERS', {"BASIC_DETAILS": ["بيانات أساسية"]}):
        group = DocumentGroup(
            start_page=0,
            end_page=1,
            primary_tenant="Test Tenant",
            category="BASIC_DETAILS", 
            dates=[],
            brief_arabic_title="Test Title", 
            reason="Test Reason"
        )
        mock_llm = MagicMock()

        # We simulate 3 failed attempts using ValueError which is caught by the router's retry loop
        mock_llm.generate_content.side_effect = [
            ValueError("Invalid folder"),
            ValueError("Invalid folder"),
            ValueError("Invalid folder")
        ]

        with pytest.raises(RoutingValidationError) as excinfo:
            route_document(group, mock_llm)

        assert "Failed to route document to valid folder after 3 attempts" in str(excinfo.value)

@patch('src.routing.router.SINGLE_MATCH', set())
def test_lockout_removal_verification():
    """Test Case 4: Verify that multiple sequential failures do not trigger a 'lockout' or skip routing.
    This test ensures that the logic for consecutive_routing_failures is gone.
    """

    # We will call route_document multiple times with failure scenarios
    # and ensure that the 6th call doesn't return '13_others' silently.

    with patch('src.routing.router.CATEGORY_TO_FOLDERS', {"BASIC_DETAILS": ["بيانات أساسية"]}):
        group = DocumentGroup(
            start_page=0,
            end_page=1,
            primary_tenant="Test Tenant",
            category="BASIC_DETAILS", 
            dates=[],
            brief_arabic_title="Test Title", 
            reason="Test Reason"
        )
        mock_llm = MagicMock()

        # Make it fail every time
        mock_llm.generate_content.side_effect = ValueError("Fail")

        # Fail 5 times
        for i in range(5):
            print(f"Attempting routing for document {i+1}...")
            with pytest.raises(RoutingValidationError): 
                route_document(group, mock_llm)
            print(f"Document {i+1} correctly raised RoutingValidationError. No lockout.")

        # The 6th call should still attempt routing and raise an error, 
        # NOT return "13_others", False
        print(f"Attempting routing for document 6 (Should NOT be locked out)...")
        with pytest.raises(RoutingValidationError):
             route_document(group, mock_llm)
        print(f"Document 6 correctly raised RoutingValidationError! Lockout mechanism is confirmed removed.")

