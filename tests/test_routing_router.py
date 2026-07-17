"""Tests for the routing engine including constrained routing and double-check logic."""

import pytest
from src.routing.router import route_document, RoutingValidationError, double_check_others
from src.routing.config import SINGLE_MATCH, FOLDER_ROUTING, CATEGORY_TO_FOLDERS, FORM_CATEGORIES, LETTER_CATEGORIES
from src.core.schemas import DocumentGroup
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

class MockLLMClient:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
        self.calls = []
        
    def generate_content(self, contents, model=None, response_schema=None, config=None, **kwargs):
        self.calls.append({"contents": contents, "model": model})
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            if isinstance(resp, Exception):
                raise resp
            if response_schema:
                if isinstance(resp, tuple):
                    data = {"selected_folder": resp[0], "reason": resp[1]}
                else:
                    data = {"selected_folder": resp, "reason": "mock reason"}
                
                return response_schema.model_validate(data, context=kwargs.get('validation_context', {}))
            return resp
        raise Exception("No more mock responses")

def test_constrained_routing_success():
    """Test that a category in FORM_CATEGORIES is constrained to FORM_FOLDERS."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="BASIC_DETAILS", dates=["2023-01-01"],
        brief_arabic_title="Test Form", reason="Form test"
    )
    # Force it to not be in SINGLE_MATCH for this test to exercise LLM
    with patch("src.routing.router.SINGLE_MATCH", set()):
        llm = MockLLMClient([("بيانات أساسية", "Correct form folder")])
        folder, direct = route_document(group, llm)
        assert folder == "بيانات أساسية"
        assert direct is False
        assert llm.call_count == 1

def test_constrained_routing_invalid_retry():
    """Test that LLM returning a folder OUTSIDE constrained list triggers retry."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="BASIC_DETAILS", dates=["2023-01-01"]
    )
    with patch("src.routing.router.SINGLE_MATCH", set()):
        # 1st: folder not in FORM_FOLDERS, 2nd: valid folder
        llm = MockLLMClient([("أمر تخصيص", "Wrong category folder"), ("بيانات أساسية", "Correct folder")])
        folder, direct = route_document(group, llm)
        assert folder == "بيانات أساسية"
        assert llm.call_count == 2

def test_constrained_routing_escape_hatch():
    """Test that 'None of the above' triggers the double-check flow."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="BASIC_DETAILS", dates=["2023-01-01"],
        brief_arabic_title="Edge Case Form"
    )
    with patch("src.routing.router.SINGLE_MATCH", set()):
        # 1st: Escape hatch, 2nd: Double-check initial, 3rd: Double-check confirmation
        llm = MockLLMClient([
            ("None of the above", "Doesn't fit"),
            ("صيانة", "Actually fits maintenance"),
            ("صيانة", "Confirmed")
        ])
        folder, direct = route_document(group, llm)
        assert folder == "صيانة"
        assert llm.call_count == 3

def test_others_flow_immediate_misc():
    """Test 'OTHER_LETTERS' category where LLM immediately picks 'رسائل متنوعة'."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="OTHER_LETTERS", dates=["2023-01-01"]
    )
    # 1st call: pick Miscellaneous
    llm = MockLLMClient([("رسائل متنوعة", "Clearly misc")])
    folder, direct = route_document(group, llm)
    assert folder == "رسائل متنوعة"
    assert llm.call_count == 1

def test_others_flow_confirm_success():
    """Test 'OTHER_LETTERS' where LLM picks a folder and confirms it."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="OTHER_LETTERS", dates=["2023-01-01"]
    )
    # 1st call: pick 'صيانة', 2nd call: confirm 'صيانة'
    llm = MockLLMClient([("صيانة", "Actually fits"), ("صيانة", "Yes confirmed")])
    folder, direct = route_document(group, llm)
    assert folder == "صيانة"
    assert llm.call_count == 2

def test_others_flow_confirm_change_mind():
    """Test 'OTHER_LETTERS' where LLM picks a folder but changes mind to 'رسائل متنوعة'."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="OTHER_LETTERS", dates=["2023-01-01"]
    )
    # 1st call: pick 'صيانة', 2nd call: pick 'رسائل متنوعة'
    llm = MockLLMClient([("صيانة", "Actually fits"), ("رسائل متنوعة", "Actually not sure")])
    folder, direct = route_document(group, llm)
    assert folder == "رسائل متنوعة"
    assert llm.call_count == 2

def test_others_flow_hallucination_fallback():
    """Test 'OTHER_LETTERS' where LLM returns an invalid folder during confirmation."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="OTHER_LETTERS", dates=["2023-01-01"]
    )
    # 1st call: pick 'صيانة', 2nd call: hallucinate 'RandomFolder'
    llm = MockLLMClient([("صيانة", "Actually fits"), ("RandomFolder", "I hallucinated")])
    folder, direct = route_document(group, llm)
    assert folder == "رسائل متنوعة"
    assert llm.call_count == 2

def test_others_flow_llm_failure_fallback():
    """Test that double_check_others falls back to 'رسائل متنوعة' on LLM exception."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="OTHER_LETTERS", dates=["2023-01-01"]
    )
    llm = MockLLMClient([Exception("API Down")])
    folder, direct = route_document(group, llm)
    assert folder == "رسائل متنوعة"
    assert llm.call_count == 1

def test_constrained_routing_max_retries():
    """Test that constrained routing fails after 3 unsuccessful attempts."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="BASIC_DETAILS", dates=["2023-01-01"]
    )
    with patch("src.routing.router.SINGLE_MATCH", set()):
        # 3 invalid responses
        llm = MockLLMClient([("invalid_1", "wrong"), ("invalid_2", "wrong"), ("invalid_3", "wrong")])
        with pytest.raises(RoutingValidationError):
            route_document(group, llm)
        assert llm.call_count == 3

def test_routing_model_propagation():
    """Test that the 'model' parameter is passed to the LLM client in route_document."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="BASIC_DETAILS", dates=["2023-01-01"]
    )
    test_model = "gpt-4o-mini"
    with patch("src.routing.router.SINGLE_MATCH", set()):
        llm = MockLLMClient([("بيانات أساسية", "Correct folder")])
        route_document(group, llm, model=test_model)
        assert llm.calls[0]["model"] == test_model

def test_double_check_model_propagation():
    """Test that the 'model' parameter is passed to the LLM client in double_check_others."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="others", dates=["2023-01-01"]
    )
    test_model = "claude-3-5-sonnet"
    llm = MockLLMClient([("صيانة", "fits"), ("صيانة", "confirmed")])
    double_check_others(group, llm, model=test_model)
    assert llm.calls[0]["model"] == test_model
    assert llm.calls[1]["model"] == test_model
