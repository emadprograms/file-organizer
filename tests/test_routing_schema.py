import pytest
from pydantic import ValidationError
from src.processing.routing.router import RoutingResponse

def test_routing_response_valid_folder():
    """Verify that RoutingResponse succeeds when selected_folder is in the allowed list."""
    data = {
        "selected_folder": "1_requests_and_applications",
        "reason": "This is a request form."
    }
    context = {"allowed_folders": ["1_requests_and_applications", "13_others"]}
    
    # Should not raise ValidationError
    response = RoutingResponse.model_validate(data, context=context)
    assert response.selected_folder == "1_requests_and_applications"
    assert response.reason == "This is a request form."

def test_routing_response_invalid_folder():
    """Verify that RoutingResponse raises ValidationError when selected_folder is NOT in the allowed list."""
    data = {
        "selected_folder": "99_invalid_folder",
        "reason": "This folder does not exist."
    }
    context = {"allowed_folders": ["1_requests_and_applications", "13_others"]}
    
    with pytest.raises(ValidationError) as excinfo:
        RoutingResponse.model_validate(data, context=context)
    
    assert "Selected folder '99_invalid_folder' is not in the allowed list" in str(excinfo.value)

def test_routing_response_missing_context():
    """Verify that missing context defaults to an empty list, causing failure for any input."""
    data = {
        "selected_folder": "1_requests_and_applications",
        "reason": "This is a request form."
    }
    
    # No context provided
    with pytest.raises(ValidationError) as excinfo:
        RoutingResponse.model_validate(data)
    
    assert "is not in the allowed list: []" in str(excinfo.value)

def test_routing_response_empty_context_list():
    """Verify that an empty allowed_folders list causes failure."""
    data = {
        "selected_folder": "1_requests_and_applications",
        "reason": "This is a request form."
    }
    context = {"allowed_folders": []}
    
    with pytest.raises(ValidationError) as excinfo:
        RoutingResponse.model_validate(data, context=context)
    
    assert "is not in the allowed list: []" in str(excinfo.value)
