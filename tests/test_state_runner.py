import pytest
from unittest.mock import MagicMock
from pathlib import Path
from src.core.state import State
from src.pipeline.runner import run_cleaning_pass, run_grouping_pass, run_routing_pass
import logging

@pytest.fixture
def mock_logger():
    return logging.getLogger("test_logger")

@pytest.fixture
def mock_state(tmp_path):
    return State("test_house", tmp_path)

def test_runner_uses_single_state(mock_state, mock_logger, tmp_path, monkeypatch):
    """STATE-02 & STATE-03: Modify runner.py to use single state.json and remove 1_cleaned.json etc."""
    # Mock llm_client
    mock_llm = MagicMock()
    
    # We need to mock Pipeline to avoid actual LLM calls
    from src.core.models import PageData
    from src.core.schemas import DocumentGroup
    
    dummy_pages = [PageData(page_index=1, original_index=1, canonical_tenant="Tenant A", category="Unassigned", content_explanation="test")]
    
    class DummyPipeline:
        def __init__(self, *args, **kwargs):
            self.client = mock_llm
            
        def _clean_documents(self, *args, **kwargs):
            return dummy_pages, None
            
        def _group_documents(self, *args, **kwargs):
            return [DocumentGroup(group_id="group1", documents=[], tenant="Tenant A", category="Unassigned", start_page=1, end_page=1, primary_tenant="Tenant A", dates=[])]
            
        def _route_documents(self, *args, **kwargs):
            return [DocumentGroup(group_id="group1", documents=[], tenant="Tenant A", category="Assigned", start_page=1, end_page=1, primary_tenant="Tenant A", dates=[])]
            
    import src.pipeline.pipeline
    monkeypatch.setattr(src.pipeline.pipeline, "Pipeline", DummyPipeline)
    
    json_path = tmp_path / "test_report.json"
    target_dir = tmp_path / "target"
    
    # 1. Cleaning pass
    cleaned_pages, _ = run_cleaning_pass(json_path, mock_state, mock_llm, mock_logger, False, "test_house", target_dir)
    assert mock_state.data["cleaned_pages"] is not None
    assert mock_state.data["cleaned_pages"][0]["canonical_tenant"] == "Tenant A"
    
    # Ensure no legacy JSONs were created
    assert list(tmp_path.glob("*.json")) == [mock_state.state_file]
    
    # 2. Grouping pass
    groups = run_grouping_pass(cleaned_pages, mock_state, "test_house", target_dir, mock_llm, mock_logger, False)
    assert mock_state.data["grouped_documents"] is not None
    assert len(mock_state.data["grouped_documents"]) == 1
    
    # 3. Routing pass
    routed = run_routing_pass(groups, mock_state, "test_house", target_dir, mock_llm, mock_logger, False)
    assert mock_state.data["routed_documents"] is not None
    assert mock_state.data["routed_documents"][0]["category"] == "Assigned"
    
    # Check that state.json exists and holds all data
    assert mock_state.state_file.exists()
