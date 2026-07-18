from typing import Any
import json
import os
import pytest
from unittest.mock import MagicMock
from src.grouping.core import process_with_shrink
from src.core.schemas import DocumentGroup

class Page:
    """Mock Page class that mimics the attributes used by process_with_shrink."""
    def __init__(self, index, data) -> Any:
        """
        Provide the   init   fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        self.original_index = int(index)
        self.category = data.get("category", "unknown")
        self.canonical_tenant = data.get("expected_tenant_name", "Unknown Tenant")
        self.resolved_date = data.get("date", "Unknown Date")
        self.date = data.get("date", "Unknown Date")
        self.content_explanation = data.get("content_explanation", "")
        self.subject = data.get("subject", "")

def test_e2e_default_routing() -> None:
    """
    Test e2e default routing.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    json_path = "pdfs/1273/567_report.json"
    if not os.path.exists(json_path):
        pytest.skip(f"Report file not found at {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    target_pages = ["194", "195", "196"]
    pages = []
    for p_idx in target_pages:
        page_data = data.get(p_idx)
        if page_data:
            pages.append(Page(p_idx, page_data))
    
    mock_llm_client = MagicMock()
    from src.core.schemas import GroupingResponse, GroupEntry
    
    mock_response = GroupingResponse(
        groups=[
            GroupEntry(start_page=194, end_page=195, primary_tenant="Tenant A", dates=[], reason="Group 1"),
            GroupEntry(start_page=196, end_page=196, primary_tenant="Tenant B", dates=[], reason="Group 2")
        ]
    )
    mock_llm_client.generate_content.return_value = mock_response

    groups = process_with_shrink(pages, mock_llm_client)

    group_194_195 = any(g.start_page == 194 and g.end_page == 195 for g in groups)
    group_196 = any(g.start_page == 196 and g.end_page == 196 for g in groups)
    
    assert group_194_195, "Pages 194-195 should be grouped together"
    assert group_196, "Page 196 should be separate"
