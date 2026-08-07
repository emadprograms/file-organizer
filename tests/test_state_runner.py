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

def test_generation_pass_does_not_overwrite_manifest(mock_logger, tmp_path, monkeypatch):
    """Test that run_generation_pass reloads state from disk before saving, so it doesn't overwrite manifest."""
    from src.pipeline.runner import run_generation_pass
    from src.core.schemas import DocumentGroup
    from src.core.state import State
    import src.pipeline.runner

    def mock_run_reconciliation(*args, **kwargs):
        house_dir = kwargs.get('house_dir') or args[4]
        house_id = kwargs.get('house_id') or args[3]
        source_files_dir = house_dir / ".source_files"
        source_files_dir.mkdir(parents=True, exist_ok=True)
        new_state = State(house_id, source_files_dir)
        new_state.data["manifest"] = {"summary": {"total_input_pages": 10}}
        new_state.save()

    import src.timeline
    monkeypatch.setattr(src.timeline, "run_reconciliation", mock_run_reconciliation)

    house_id = "test_house"
    output_dir = tmp_path
    house_dir = output_dir / house_id
    house_dir.mkdir(parents=True, exist_ok=True)
    
    source_files_dir = house_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    
    mock_state = State(house_id, source_files_dir)
    assert mock_state.data.get("manifest") is None

    docs = [DocumentGroup(group_id="group1", documents=[], tenant="Tenant A", category="Assigned", start_page=1, end_page=1, primary_tenant="Tenant A", dates=[])]

    import src.pdf.compress
    monkeypatch.setattr(src.pdf.compress, "compress_pdf", lambda *args, **kwargs: None)
    
    class MockOrganizer:
        def organize(self, *args, **kwargs):
            return [{"output_file": "doc_1.pdf"}], house_id
            
    monkeypatch.setattr("src.timeline.FileOrganizer", lambda: MockOrganizer())
    
    dummy_pdf = tmp_path / "dummy.pdf"
    dummy_pdf.touch()

    class MockFitz:
        def __init__(self, *args, **kwargs):
            self.page_count = 10
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    monkeypatch.setattr("fitz.open", MockFitz)

    run_generation_pass(
        documents=docs,
        target_dir=output_dir,
        house_id=house_id,
        output_dir=output_dir,
        logger=mock_logger,
        dry_run=False,
        json_path=tmp_path / "dummy.json",
        yaml_data=None,
        pdf_path=dummy_pdf,
        fixed_house_dir=house_dir,
        prepend_manifest=False,
        state=mock_state
    )

    final_state = State(house_id, source_files_dir)
    assert final_state.data.get("manifest") is not None
    assert final_state.data["manifest"]["summary"]["total_input_pages"] == 10
