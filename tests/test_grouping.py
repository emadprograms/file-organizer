import pytest
from src.processing.grouping import verify_groups, merge_chunks
from src.core.schemas import GroupEntry, DocumentGroup
from types import SimpleNamespace


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
