"""Tests for the routing engine."""

import pytest
from src.processing.routing import route_document, SINGLE_MATCH, MULTI_MATCH, FOLDER_ROUTING, CATEGORY_TO_FOLDERS
from src.core.schemas import DocumentGroup
from unittest.mock import patch, MagicMock

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
        
    def generate_content(self, model, contents, response_schema=None, config=None, **kwargs):
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            if isinstance(resp, Exception):
                raise resp
            if response_schema:
                return MockParsedResponse(resp)
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
        folder, direct = route_document(group, llm)
        assert folder == "Unassigned"
        assert direct is False
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
    """Test that if the LLM returns an invalid folder, it retries and then falls back."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"]
    )
    # Both attempts return invalid folders
    llm = MockLLMClient(["invalid_folder_1", "invalid_folder_2"])
    folder, direct = route_document(group, llm)
    
    assert folder == "13_others"
    assert direct is False
    assert llm.call_count == 2

def test_multi_match_llm_exception_fallback():
    """Test that if the LLM throws exceptions, it falls back to 13_others."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="forms", dates=["2023-01-01"]
    )
    llm = MockLLMClient([Exception("API error"), Exception("API error 2")])
    folder, direct = route_document(group, llm)
    
    assert folder == "13_others"
    assert direct is False
    assert llm.call_count == 2

def test_unknown_category_fallback():
    """Test that an unknown category falls back."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="unknown_cat", dates=["2023-01-01"]
    )
    llm = MockLLMClient([])
    folder, direct = route_document(group, llm)
    assert folder == "13_others"
    assert direct is False
    assert llm.call_count == 0

from src.processing.organizer import FileOrganizer
from pathlib import Path

def test_filename_format(monkeypatch, tmp_path):
    monkeypatch.setattr("src.processing.organizer.extract_pdf_segment", lambda s, st, e, t: None)
    
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="TestTenant",
        category="letters", dates=["2023-05-10"],
        brief_arabic_title="TestTitle", folder_path="12_tenant_correspondence",
        is_direct_routed=False,
        reason=""
    )
    
    organizer = FileOrganizer()
    output_base = tmp_path / "dummy_out"
    output_base.mkdir()
    summary = organizer.organize([group], "dummy.pdf", "dummy_house", output_base)
    
    paths = list(set([item["output_file"] for item in summary]))
    assert len(paths) == 1
    assert "2023-05-10 - TestTitle.pdf" in paths[0]

def test_dateless_filename(monkeypatch, tmp_path):
    monkeypatch.setattr("src.processing.organizer.extract_pdf_segment", lambda s, st, e, t: None)
    
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="TestTenant",
        category="letters", dates=[],
        brief_arabic_title="TestTitle", folder_path="12_tenant_correspondence",
        is_direct_routed=False,
        reason=""
    )
    
    organizer = FileOrganizer()
    output_base = tmp_path / "dummy_out"
    output_base.mkdir()
    summary = organizer.organize([group], "dummy.pdf", "dummy_house", output_base)
    
    paths = list(set([item["output_file"] for item in summary]))
    assert len(paths) == 1
    assert "nodate - TestTitle.pdf" in paths[0]
