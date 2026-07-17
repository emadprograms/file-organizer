import json
import os
import pytest
from unittest.mock import MagicMock
from src.grouping.core import process_with_shrink
from src.core.schemas import DocumentGroup

class Page:
    """Mock Page class that mimics the attributes used by process_with_shrink."""
    def __init__(self, index, data):
        self.original_index = int(index)
        self.category = data.get("category", "unknown")
        self.canonical_tenant = data.get("expected_tenant_name", "Unknown Tenant")
        self.resolved_date = data.get("date", "Unknown Date")
        self.date = data.get("date", "Unknown Date")
        self.content_explanation = data.get("content_explanation", "")
        self.subject = data.get("subject", "")

def test_e2e_continuity():
    json_path = "tests/fixtures/continuity_test_state.json"
    if not os.path.exists(json_path):
        pytest.skip(f"Fixture file not found at {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_pages = []
    for item in data:
        all_pages.append(Page(item["original_index"], item))
    
    pages = [p for p in all_pages if p.category == "letters"]
    
    # Mock LLM Client
    mock_llm_client = MagicMock()
    from src.core.schemas import GroupingResponse, GroupEntry

    def mock_generate_content(*args, **kwargs):
        prompt = kwargs.get('contents', [])[0]
        import re
        match = re.search(r"Chunk range: Page (\d+) to Page (\d+)", prompt)
        if match:
            start_idx = int(match.group(1))
            end_idx = int(match.group(2))
            # Just create a single group covering the whole chunk for simplicity,
            # or split based on actual logic. We want Story 1 (pages 1-3), Story 2 (4-6), Hard Reset (8).
            # The actual indexes in `pages` array: 
            # Original indexes: [1, 2, 3, 4, 5, 6, 8]
            # Array indexes:     0, 1, 2, 3, 4, 5, 6
            # Story 1: array idx 0-2 (orig 1-3)
            # Story 2: array idx 3-5 (orig 4-6)
            # Hard Reset: array idx 6 (orig 8)
            groups = []
            if start_idx <= 2:
                groups.append(GroupEntry(start_page=max(start_idx, 0), end_page=min(end_idx, 2), primary_tenant="Tenant A", dates=[], reason="Story 1", brief_arabic_title="Test"))
            if end_idx >= 3 and start_idx <= 5:
                groups.append(GroupEntry(start_page=max(start_idx, 3), end_page=min(end_idx, 5), primary_tenant="Tenant A", dates=[], reason="Story 2", brief_arabic_title="Test"))
            if end_idx >= 6:
                groups.append(GroupEntry(start_page=max(start_idx, 6), end_page=min(end_idx, 6), primary_tenant="Tenant B", dates=[], reason="Hard Reset", brief_arabic_title="Test"))
            
            return GroupingResponse(groups=groups)
        return GroupingResponse(groups=[GroupEntry(start_page=0, end_page=len(pages)-1, primary_tenant="Tenant A", dates=[], reason="Fallback", brief_arabic_title="Test")])

    mock_llm_client.generate_content.side_effect = mock_generate_content

    groups = process_with_shrink(pages, mock_llm_client)

    story1_passed = False
    story2_passed = False
    hard_reset_passed = True
    
    for group in groups:
        if group.start_page <= 1 and group.end_page >= 3:
            if group.end_page < 4:
                story1_passed = True
        
        if group.start_page <= 4 and group.end_page >= 6:
            if group.end_page < 8:
                story2_passed = True
            else:
                hard_reset_passed = False

    assert story1_passed, "Story 1 (pages 1-3) failed to group correctly"
    assert story2_passed, "Story 2 (pages 4-6) failed to group correctly"
    assert hard_reset_passed, "Hard reset (page 8) was incorrectly merged"
