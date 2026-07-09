"""Tests for the routing engine."""

import pytest
from src.processing.routing.router import route_document, RoutingValidationError
from src.processing.routing.config import SINGLE_MATCH, FOLDER_ROUTING, CATEGORY_TO_FOLDERS
from src.core.schemas import DocumentGroup
from unittest.mock import patch, MagicMock
import pytest

class MockParsedResponse:
    def __init__(self, selected_folder, reason="mock reason"):
        if isinstance(selected_folder, tuple):
            self.selected_folder = selected_folder[0]
            self.reason = selected_folder[1]
        else:
            self.selected_folder = selected_folder
            self.reason = reason


class MockParsedResponse:
    def __init__(self, selected_folder, reason="mock reason"):
        if isinstance(selected_folder, tuple):
            self.selected_folder = selected_folder[0]
            self.reason = selected_folder[1]
        else:
            self.selected_folder = selected_folder
            self.reason = reason

class MockResponse:
    def __init__(self, parsed):
        self.parsed = parsed

class MockLLMClient:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
        self.calls = []
        
    def generate_content(self, contents, model=None, response_schema=None, config=None, **kwargs):
        self.calls.append(contents)
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            if isinstance(resp, Exception):
                raise resp
            if response_schema:
                # If resp is a tuple (folder, reason), use it. Otherwise assume it's the folder.
                if isinstance(resp, tuple):
                    data = {"selected_folder": resp[0], "reason": resp[1]}
                else:
                    data = {"selected_folder": resp, "reason": "mock reason"}
                
                # Use model_validate with context to trigger Pydantic validators
                return response_schema.model_validate(data, context=kwargs.get('validation_context', {}))
            return MockResponse(resp)
        raise Exception("No more mock responses")

def test_routing_dict():
    """Test that the hardcoded dictionary is defined correctly."""
    assert "13_others" in FOLDER_ROUTING
    assert "1_requests_and_applications" in FOLDER_ROUTING
    
    assert CATEGORY_TO_FOLDERS["contract"] == ["5_contract"]
    
def test_single_match_direct():
    """Test that single-match categories bypass the LLM."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="contract", dates=["2023-01-01"]
    )
    llm = MockLLMClient([Exception("Should not be called")])
    folder, direct = route_document(group, llm)
    
    assert folder == "5_contract"
    assert direct is True
    assert llm.call_count == 0

def test_single_match_index_error():
    """Test that IndexError during folder mapping falls back to Unassigned."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="contract", dates=["2023-01-01"]
    )
    llm = MockLLMClient([])
    # Temporarily remove the mapping to trigger IndexError
    original_mapping = CATEGORY_TO_FOLDERS.get("contract")
    CATEGORY_TO_FOLDERS["contract"] = []
    try:
        with pytest.raises(RoutingValidationError):
            route_document(group, llm)
    finally:
        CATEGORY_TO_FOLDERS["contract"] = original_mapping
def test_multi_match_llm(monkeypatch):
    """Test that multi-match categories use the LLM and return a valid folder and reason."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"],
        brief_arabic_title="Complaint about water leak",
        reason="Talks about a water leak"
    )
    # Mock the LLM to return the folder and a specific reason
    llm = MockLLMClient([("8_complaints_and_violations", "Explicit explanation for routing")])

    # Mock log_decision_trace to verify it's called
    with patch("src.logger.log_decision_trace") as mock_trace:
        folder, direct = route_document(group, llm)

        assert folder == "8_complaints_and_violations"
        assert direct is False
        assert llm.call_count == 1

        # Verify the trace call: log_decision_trace("routing", {category, selected, reason})
        mock_trace.assert_called_once()
        args, _ = mock_trace.call_args
        assert args[0] == "routing"
        assert args[1]["category"] == "letters"
        assert args[1]["selected"] == "8_complaints_and_violations"
        assert args[1]["reason"] == "Explicit explanation for routing"

def test_multi_match_llm_retry_on_invalid():
    """Test that if the LLM returns an invalid folder, it retries 3 times and then raises RoutingValidationError."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"]
    )
    # 3 attempts return invalid folders
    llm = MockLLMClient(["invalid_folder_1", "invalid_folder_2", "invalid_folder_3"])
    
    with pytest.raises(RoutingValidationError):
        route_document(group, llm)
    
    assert llm.call_count == 3

def test_multi_match_llm_retry_success():
    """Test that if the LLM returns invalid folders but then a valid one, it succeeds."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"]
    )
    # 2 invalid, 1 valid
    llm = MockLLMClient(["invalid_1", "invalid_2", "8_complaints_and_violations"])
    
    folder, direct = route_document(group, llm)
    
    assert folder == "8_complaints_and_violations"
    assert direct is False
    assert llm.call_count == 3

def test_multi_match_llm_feedback_prompt():
    """Test that the feedback prompt is correctly constructed and passed to the LLM on retries."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"]
    )
    # 1 invalid, then 1 valid
    llm = MockLLMClient(["invalid_folder_xyz", "8_complaints_and_violations"])
    
    route_document(group, llm)
    
    assert llm.call_count == 2
    # The second call should contain the feedback about the first invalid folder
    second_call_contents = llm.calls[1]
    # We check if any of the content parts contain the feedback message
    feedback_found = False
    if isinstance(second_call_contents, list):
        for part in second_call_contents:
            if "invalid_folder_xyz" in str(part) and "not in the allowed list" in str(part):
                feedback_found = True
                break
    elif "invalid_folder_xyz" in str(second_call_contents) and "not in the allowed list" in str(second_call_contents):
        feedback_found = True
        
    assert feedback_found, "Feedback prompt for invalid folder was not found in the retry call"

def test_multi_match_llm_exception_fallback():
    """Test that if the LLM throws exceptions, it retries 3 times and then raises RoutingValidationError."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="forms", dates=["2023-01-01"]
    )
    llm = MockLLMClient([Exception("API error"), Exception("API error 2"), Exception("API error 3")])
    
    with pytest.raises(RoutingValidationError):
        route_document(group, llm)
    
    assert llm.call_count == 3


def test_unknown_category_fallback():
    """Test that an unknown category falls back."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="unknown_cat", dates=["2023-01-01"]
    )
    llm = MockLLMClient([])
    with pytest.raises(RoutingValidationError):
        route_document(group, llm)

from src.processing.organizer import FileOrganizer
from pathlib import Path

def test_filename_format(monkeypatch, tmp_path):
    # Create a dummy PDF so fitz.open doesn't fail
    import fitz
    dummy_pdf = tmp_path / "dummy.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(dummy_pdf))
    doc.close()

    monkeypatch.setattr("src.processing.pdf.extract.extract_pdf_segment", lambda s, st, e, t: None)
    
    group = DocumentGroup(
        start_page=0, end_page=0, primary_tenant="TestTenant",
        category="letters", dates=["2023-05-10"],
        brief_arabic_title="TestTitle", folder_path="12_tenant_correspondence",
        is_direct_routed=False,
        reason=""
    )
    
    organizer = FileOrganizer()
    output_base = tmp_path / "dummy_out"
    output_base.mkdir()
    summary = organizer.organize([group], str(dummy_pdf), "dummy_house", output_base)
    
    paths = list(set([item["output_file"] for item in summary]))
    assert len(paths) == 1
    assert "2023-05-10 - TestTitle.pdf" in paths[0]

def test_dateless_filename(monkeypatch, tmp_path):
    # Create a dummy PDF so fitz.open doesn't fail
    import fitz
    dummy_pdf = tmp_path / "dummy.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(dummy_pdf))
    doc.close()

    monkeypatch.setattr("src.processing.pdf.extract.extract_pdf_segment", lambda s, st, e, t: None)
    
    group = DocumentGroup(
        start_page=0, end_page=0, primary_tenant="TestTenant",
        category="letters", dates=[],
        brief_arabic_title="TestTitle", folder_path="12_tenant_correspondence",
        is_direct_routed=False,
        reason=""
    )
    
    organizer = FileOrganizer()
    output_base = tmp_path / "dummy_out"
    output_base.mkdir()
    summary = organizer.organize([group], str(dummy_pdf), "dummy_house", output_base)
    
    paths = list(set([item["output_file"] for item in summary]))
    assert len(paths) == 1
    assert "nodate - TestTitle.pdf" in paths[0]
