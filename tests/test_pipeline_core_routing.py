from typing import Any
import pytest
import os
import hashlib
import json
from unittest.mock import MagicMock, patch, call
from src.pipeline.pipeline import Pipeline, PageData
from src.core.schemas import DocumentGroup
from src.routing.state import RoutingState

def compute_checksum(documents: list[DocumentGroup]) -> str:
    """Helper to compute checksum based on document boundaries and categories."""
    hasher = hashlib.sha256()
    for doc in documents:
        # We use start_page, end_page, and category to uniquely identify the grouping
        data = f"{doc.start_page}:{doc.end_page}:{doc.category}"
        hasher.update(data.encode("utf-8"))
    return hasher.hexdigest()

@pytest.fixture
def mock_llm_client() -> None:
    """
    Provide the mock llm client fixture/mock.

    Returns:
    The appropriate fixture or mock value.
    """
    with patch("src.pipeline.pipeline.LLMClient") as mock:
        yield mock.return_value

@pytest.fixture
def pipeline(mock_llm_client) -> Any:
    """
    Provide the pipeline fixture/mock.

    Returns:
    The appropriate fixture or mock value.
    """
    return Pipeline(api_key="test_key")

@pytest.fixture
def sample_docs() -> Any:
    """
    Provide the sample docs fixture/mock.

    Returns:
    The appropriate fixture or mock value.
    """
    return [
        DocumentGroup(start_page=0, end_page=0, category="cat1", primary_tenant="tenant1", dates=[], canonical_tenant="tenant1"),
        DocumentGroup(start_page=1, end_page=1, category="cat1", primary_tenant="tenant1", dates=[], canonical_tenant="tenant1"),
        DocumentGroup(start_page=2, end_page=2, category="cat2", primary_tenant="tenant2", dates=[], canonical_tenant="tenant2"),
    ]

def test_resumption_persistence(tmp_path, pipeline, sample_docs) -> None:
    """Task 1: Verify that resuming routing restores all previously assigned folder paths (Fixes Skip-and-Forget)."""
    checkpoint_path = str(tmp_path / "run_checkpoint.json")
    
    # 1. Run routing for only a subset of documents
    with patch("src.routing.route_document") as mock_route:
        # Only return results for the first 2 documents, then simulate an interruption
        mock_route.side_effect = [
            ("folder/1", False),
            ("folder/2", False),
            Exception("Interrupted!"),
        ]
        
        try:
            pipeline._route_documents(sample_docs, run_checkpoint_path=checkpoint_path)
        except Exception as e:
            assert str(e) == "Interrupted!"

    # Verify that _routing.json exists and contains the results for first 2 docs
    routing_checkpoint = checkpoint_path.replace(".json", "_routing.json")
    assert os.path.exists(routing_checkpoint)
    
    # 2. Resume routing with a new pipeline instance
    new_pipeline = Pipeline(api_key="test_key")
    
    with patch("src.routing.route_document") as mock_route_resumed:
        mock_route_resumed.return_value = ("folder/3", False)
        
        # Re-run routing. The first 2 should be restored from state, the 3rd should be routed.
        final_docs = new_pipeline._route_documents(sample_docs, run_checkpoint_path=checkpoint_path)
        
        # Check results
        assert final_docs[0].folder_path == "folder/1"
        assert final_docs[1].folder_path == "folder/2"
        assert final_docs[2].folder_path == "folder/3"
        
        # route_document should only have been called ONCE for the 3rd document
        assert mock_route_resumed.call_count == 1

def test_model_parameter_passed(tmp_path, mock_llm_client) -> None:
    """Task 2: Verify that the designated routing model is actually used by the LLM client."""
    test_model = "test-model-123"
    pipeline = Pipeline(api_key="test_key", routing_model=test_model)
    
    doc = DocumentGroup(start_page=0, end_page=0, category="cat1", primary_tenant="tenant1", dates=[], canonical_tenant="tenant1")
    
    with patch("src.routing.route_document") as mock_route:
        # Mock the return value of route_document
        mock_route.return_value = ("folder/path", False)
        
        pipeline._route_documents([doc], run_checkpoint_path=None)
        
        # Verify route_document was called with the correct model
        # The call is route_document(doc, self.client, model=self.routing_model)
        mock_route.assert_called_once_with(doc, pipeline.client, model=test_model)

def test_routing_sanity_check_grouping_mismatch(tmp_path, pipeline, sample_docs) -> None:
    """Task 3: Verify that modifying grouping results triggers a full routing reset (D-04)."""
    checkpoint_path = str(tmp_path / "run_checkpoint.json")
    routing_checkpoint = checkpoint_path.replace(".json", "_routing.json")
    
    # 1. Run routing for a subset and create a checkpoint
    with patch("src.routing.route_document") as mock_route:
        mock_route.side_effect = [
            ("folder/1", False),
            Exception("Interrupted!"),
        ]
        try:
            pipeline._route_documents(sample_docs, run_checkpoint_path=checkpoint_path)
        except Exception:
            pass
    
    assert os.path.exists(routing_checkpoint)
    
    # 2. Modify the documents so that the checksum changes
    # Change category of one document
    sample_docs[0].category = "NEW_CATEGORY"
    
    # 3. Resume routing
    with patch("src.routing.route_document") as mock_route_resumed:
        mock_route_resumed.return_value = ("folder/reset", False)
        
        pipeline._route_documents(sample_docs, run_checkpoint_path=checkpoint_path)
        
        # Because checksum changed, it should route ALL documents from the beginning
        # sample_docs has 3 elements.
        assert mock_route_resumed.call_count == 3
        
        # Verify all got the reset folder
        for doc in sample_docs:
            assert doc.folder_path == "folder/reset"
