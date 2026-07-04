"""Tests for the routing engine."""

import pytest
from src.processing.routing import route_document, SINGLE_MATCH, MULTI_MATCH, FOLDER_ROUTING, CATEGORY_TO_FOLDERS
from src.core.schemas import DocumentGroup

class MockRoutingResponse:
    def __init__(self, selected_folder):
        self.selected_folder = selected_folder

class MockLLMClient:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
        
    def _route_llm_call(self, model, contents, response_schema, log_prefix=None, max_attempts=None):
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            if isinstance(resp, Exception):
                raise resp
            return MockRoutingResponse(resp)
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

def test_multi_match_llm():
    """Test that multi-match categories use the LLM and return a valid folder."""
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"],
        brief_arabic_title="Complaint about water leak",
        reason="Talks about a water leak"
    )
    llm = MockLLMClient(["8_complaints_and_violations"])
    folder, direct = route_document(group, llm)
    
    assert folder == "8_complaints_and_violations"
    assert direct is False
    assert llm.call_count == 1

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

def test_filename_format(monkeypatch):
    monkeypatch.setattr("src.processing.organizer.extract_pdf_segment", lambda s, st, e, t: None)
    
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="TestTenant",
        category="letters", dates=["2023-05-10"],
        brief_arabic_title="TestTitle", folder_path="12_tenant_correspondence",
        is_direct_routed=False,
        reason=""
    )
    
    organizer = FileOrganizer()
    summary = organizer.organize([group], "dummy.pdf", Path("dummy_out"), None)
    
    paths = list(summary.keys())
    assert len(paths) == 1
    assert "2023-05-10 - TestTitle.pdf" in paths[0]

def test_dateless_filename(monkeypatch):
    monkeypatch.setattr("src.processing.organizer.extract_pdf_segment", lambda s, st, e, t: None)
    
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="TestTenant",
        category="letters", dates=[],
        brief_arabic_title="TestTitle", folder_path="12_tenant_correspondence",
        is_direct_routed=False,
        reason=""
    )
    
    organizer = FileOrganizer()
    summary = organizer.organize([group], "dummy.pdf", Path("dummy_out"), None)
    
    paths = list(summary.keys())
    assert len(paths) == 1
    assert "nodate - TestTitle.pdf" in paths[0]
