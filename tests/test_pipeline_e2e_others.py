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

def test_e2e_others_precision() -> None:
    """
    Test e2e others precision.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    json_path = "pdfs/1273/567_report.json"
    if not os.path.exists(json_path):
        pytest.skip(f"Report file not found at {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pages = []
    for i in range(30, 34):
        page_data = data.get(str(i))
        if page_data:
            pages.append(Page(i, page_data))
    
    mock_llm_client = MagicMock()
    from src.core.schemas import GroupingResponse, GroupEntry
    
    # process_with_shrink calls _process_chunk in chunks.
    # We mock _process_chunk instead to avoid deep mocking of LLM calls in chunks
    from unittest.mock import patch
    with patch('src.grouping.core._process_chunk') as mock_process_chunk:
        mock_process_chunk.return_value = [
            DocumentGroup(start_page=30, end_page=33, primary_tenant="T", category="others", dates=[], reason="R")
        ]
        
        groups = process_with_shrink(pages, mock_llm_client)

    found_single_group = len(groups) == 1 and groups[0].start_page == 30 and groups[0].end_page == 33
    assert found_single_group, f"Expected 1 group (30-33), but found {len(groups)} groups"
