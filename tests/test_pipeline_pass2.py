import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace

from src.processing.pipeline import Pipeline
from src.core.schemas import DocumentGroup, GroupEntry, GroupingResponse

class PageData(SimpleNamespace):
    def model_dump(self):
        return self.__dict__

def test_category_presplit():
    pipeline = Pipeline("dummy_key")
    
    # 4 pages: first 2 are forms, next 2 are letters
    # Wait, the pipeline splits by category AND residents[0]
    p0 = PageData(category="forms", residents=["Ahmed"], date="2024-01-01", summary="")
    p1 = PageData(category="forms", residents=["Ahmed"], date="2024-01-02", summary="")
    p2 = PageData(category="letters", residents=["Ahmed"], date="2024-01-03", summary="")
    p3 = PageData(category="forms", residents=["Ali"], date="2024-01-04", summary="")
    
    raw_pages = [(0, p0), (1, p1), (2, p2), (3, p3)]
    
    # Mock llm_client
    pipeline.client = MagicMock()
    
    # Mock grouping process to just return one group per run
    from src.processing import grouping
    original_process = grouping.process_with_shrink
    
    called_runs = []
    
    def fake_process_with_shrink(run, client):
        called_runs.append(run)
        return [DocumentGroup(
            start_page=0, end_page=len(run)-1,
            primary_tenant="Ahmed", category=run[0].category,
            dates=[], reason="mock", brief_arabic_title="mock"
        )]
        
    grouping.process_with_shrink = fake_process_with_shrink
    
    try:
        pipeline._group_and_route_documents(raw_pages, None)
        
        assert len(called_runs) == 3
        # Run 1: forms, Ahmed
        assert len(called_runs[0]) == 2
        assert called_runs[0][0].category == "forms"
        # Run 2: letters, Ahmed
        assert len(called_runs[1]) == 1
        assert called_runs[1][0].category == "letters"
        # Run 3: forms, Ali
        assert len(called_runs[2]) == 1
        assert called_runs[2][0].category == "forms"
        assert called_runs[2][0].residents[0] == "Ali"
    finally:
        grouping.process_with_shrink = original_process

def test_routing_integration():
    pipeline = Pipeline("dummy_key")
    
    # 2 pages of category "contract" (single match) -> "5_contract"
    p0 = PageData(category="contract", residents=["Ahmed"], date="2024-01-01", summary="")
    p1 = PageData(category="contract", residents=["Ahmed"], date="2024-01-02", summary="")
    
    raw_pages = [(0, p0), (1, p1)]
    
    # Mock LLM Client
    mock_client = MagicMock()
    pipeline.client = mock_client
    
    # We don't mock grouping.process_with_shrink, we mock the LLM call inside it
    mock_client._route_llm_call.return_value = GroupingResponse(
        groups=[
            GroupEntry(start_page=0, end_page=1, reason="Test", brief_arabic_title="Test Title")
        ]
    )
    
    result = pipeline._group_and_route_documents(raw_pages, None)
    
    assert len(result) == 1
    doc = result[0]
    assert doc.start_page == 0
    assert doc.end_page == 1
    assert doc.folder_path == "5_contract"
    assert doc.primary_tenant == "Ahmed" # Derived from first page
    assert doc.is_direct_routed is True
