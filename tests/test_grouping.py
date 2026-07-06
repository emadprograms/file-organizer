import pytest
from src.processing.grouping import category_presplit, verify_groups, merge_chunks
from src.core.schemas import GroupEntry, DocumentGroup
from types import SimpleNamespace

def test_category_presplit():
    pages = [
        SimpleNamespace(category="forms", page_idx=0),
        SimpleNamespace(category="forms", page_idx=1),
        SimpleNamespace(category="letters", page_idx=2),
        SimpleNamespace(category="letters", page_idx=3),
        SimpleNamespace(category="forms", page_idx=4),
    ]
    
    runs = category_presplit(pages)
    assert len(runs) == 3
    assert len(runs[0]) == 2
    assert runs[0][0].category == "forms"
    assert runs[1][0].category == "letters"
    assert runs[2][0].category == "forms"

def test_verification_logic():
    # Valid
    groups = [
        GroupEntry(start_page=0, end_page=2, reason="A", brief_arabic_title="A"),
        GroupEntry(start_page=3, end_page=9, reason="B", brief_arabic_title="B")
    ]
    assert verify_groups(groups, 0, 10) == True
    
    # Gap
    with pytest.raises(ValueError, match="Gap or overlap detected"):
        groups_gap = [
            GroupEntry(start_page=0, end_page=2, reason="A", brief_arabic_title="A"),
            GroupEntry(start_page=4, end_page=9, reason="B", brief_arabic_title="B")
        ]
        verify_groups(groups_gap, 0, 10)
        
    # Overlap
    with pytest.raises(ValueError, match="Gap or overlap detected"):
        groups_overlap = [
            GroupEntry(start_page=0, end_page=3, reason="A", brief_arabic_title="A"),
            GroupEntry(start_page=3, end_page=9, reason="B", brief_arabic_title="B")
        ]
        verify_groups(groups_overlap, 0, 10)
        
    # Bad start
    with pytest.raises(ValueError, match="does not match chunk_start_idx"):
        verify_groups(groups, 1, 10)
        
    # Bad end
    with pytest.raises(ValueError, match="does not match chunk end boundary"):
        verify_groups(groups, 0, 11)

def test_overlap_merge():
    # overlap_page_idx = 9
    # Chunk 1: pages 0-9
    chunk1_groups = [
        DocumentGroup(start_page=0, end_page=5, primary_tenant="T1", category="forms", dates=[]),
        DocumentGroup(start_page=6, end_page=9, primary_tenant="T1", category="forms", dates=[], reason="reason1", brief_arabic_title="title1")
    ]
    
    # Chunk 2: pages 9-15
    chunk2_groups = [
        DocumentGroup(start_page=9, end_page=12, primary_tenant="T2", category="forms", dates=[], reason="reason2", brief_arabic_title="title2"),
        DocumentGroup(start_page=13, end_page=15, primary_tenant="T2", category="forms", dates=[])
    ]
    
    merged = merge_chunks(chunk1_groups, chunk2_groups, 9)
    assert len(merged) == 3
    assert merged[0].end_page == 5
    assert merged[1].start_page == 6
    assert merged[1].end_page == 12
    assert merged[1].reason == "reason1"  # Trust chunk 1
    assert merged[1].brief_arabic_title == "title1" # Trust chunk 1
    assert merged[2].start_page == 13
    assert merged[2].end_page == 15

from src.processing.grouping import process_with_shrink, GROUPING_PROMPT
from src.core.schemas import GroupingResponse

class MockGroup:
    def __init__(self, start, end, reason, brief):
        self.start_page = start
        self.end_page = end
        self.reason = reason
        self.brief_arabic_title = brief

class MockResponse:
    def __init__(self, groups):
        self.groups = groups

class MockLLMForOverlap:
    def __init__(self):
        self.calls = []
        self.chunk_ranges = []

    def generate_content(self, model, contents, response_schema=None, is_boundary_call=False, config=None, **kwargs):
        self.calls.append(contents)
        import re
        match = re.search(r"Chunk range: Page (\d+) to Page (\d+)", contents[0])
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            self.chunk_ranges.append((start, end))
            return MockResponse([MockGroup(start, end, "reason", "title")])
        raise ValueError("Prompt doesn't match")

def test_chunk_generator_overlap():
    pages = [SimpleNamespace(category="forms", page_idx=i, date="NONE", residents=[]) for i in range(15)]
    llm = MockLLMForOverlap()
    groups = process_with_shrink(pages, llm)
    assert len(llm.chunk_ranges) == 2
    assert llm.chunk_ranges[0] == (0, 9)
    assert llm.chunk_ranges[1] == (9, 14)

def test_boundary_signals():
    assert "subject/content shift" in GROUPING_PROMPT
    assert "DO NOT split on date changes" in GROUPING_PROMPT

def test_response_has_reasoning():
    from src.core.schemas import GroupEntry
    assert "reason" in GroupEntry.model_fields
    assert "brief_arabic_title" in GroupEntry.model_fields

def test_schema_validation():
    data = {
        "groups": [
            {
                "start_page": 0,
                "end_page": 2,
                "reason": "Because",
                "brief_arabic_title": "Test"
            }
        ]
    }
    obj = GroupingResponse(**data)
    assert len(obj.groups) == 1
    assert obj.groups[0].reason == "Because"

from unittest.mock import MagicMock, patch
from src.llm_client import LLMChunkShrinkRequiredError

def test_grouping_shrink_on_error():
    """Test that process_with_shrink catches LLMChunkShrinkRequiredError and actually reduces chunk size from 10 to 5."""
    pages = [SimpleNamespace(category="forms", page_idx=i, date="NONE", residents=[]) for i in range(15)]
    
    class MockShrinkLLM:
        def __init__(self):
            self.calls = []
            
        def generate_content(self, model, contents, response_schema=None, is_boundary_call=False, config=None, **kwargs):
            self.calls.append(contents[0])
            call_count = len(self.calls)
            
            if call_count == 1:
                # First call: Should be chunk size 10 (Page 0 to 9)
                assert "Chunk range: Page 0 to Page 9" in contents[0]
                raise LLMChunkShrinkRequiredError("Shrink now")
            elif call_count == 2:
                # Second call: Should be shrunk to chunk size 5 (Page 0 to 4)
                assert "Chunk range: Page 0 to Page 4" in contents[0]
                return MockResponse([MockGroup(0, 4, "reason 1", "title 1")])
            elif call_count == 3:
                # Third call: Processing next chunk of 5 (Page 4 to 8 due to overlap=1)
                assert "Chunk range: Page 4 to Page 8" in contents[0]
                return MockResponse([MockGroup(4, 8, "reason 2", "title 2")])
            elif call_count == 4:
                # Fourth call: Processing chunk of 5 (Page 8 to 12)
                assert "Chunk range: Page 8 to Page 12" in contents[0]
                return MockResponse([MockGroup(8, 12, "reason 3", "title 3")])
            elif call_count == 5:
                # Fifth call: Processing remaining (Page 12 to 14)
                assert "Chunk range: Page 12 to Page 14" in contents[0]
                return MockResponse([MockGroup(12, 14, "reason 4", "title 4")])
            else:
                raise ValueError(f"Too many calls: {call_count}")

    llm = MockShrinkLLM()
    groups = process_with_shrink(pages, llm)
    
    assert len(llm.calls) == 5
    assert len(groups) == 1
    assert groups[0].start_page == 0
    assert groups[0].end_page == 14
