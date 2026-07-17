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
    json_path = "tests/fixtures/uat_08_continuity_data.json"
    if not os.path.exists(json_path):
        pytest.skip(f"Fixture file not found at {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_pages = []
    for i in range(1, 11):
        page_data = data.get(str(i))
        if page_data:
            all_pages.append(Page(i, page_data))
    
    pages = [p for p in all_pages if p.category == "letters"]
    
    # Mock LLM Client
    mock_llm_client = MagicMock()
    # Mock the return values for _process_chunk if necessary or let process_with_shrink run.
    # Wait, process_with_shrink uses the LLM if CHUNK_SIZES requires it. For letters, CHUNK_SIZES is [10].
    # So it calls LLM once for all pages. We need to mock generate_content to return a GroupingResponse.
    from src.core.schemas import GroupingResponse, GroupEntry
    
    mock_response = GroupingResponse(
        groups=[
            GroupEntry(start_page=1, end_page=3, primary_tenant="Tenant A", dates=[], reason="Story 1"),
            GroupEntry(start_page=4, end_page=6, primary_tenant="Tenant A", dates=[], reason="Story 2"),
            GroupEntry(start_page=8, end_page=8, primary_tenant="Tenant B", dates=[], reason="Hard Reset")
        ]
    )
    mock_llm_client.generate_content.return_value = mock_response

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
