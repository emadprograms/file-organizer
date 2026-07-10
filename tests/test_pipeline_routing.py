import pytest
import os
import hashlib
import json
from unittest.mock import MagicMock, patch
from src.processing.pipeline import Pipeline, PageData
from src.core.schemas import DocumentGroup
from src.processing.routing.state import RoutingState

def compute_checksum(documents: list[DocumentGroup]) -> str:
    """Helper to compute checksum based on document boundaries and categories."""
    hasher = hashlib.sha256()
    for doc in documents:
        # We use start_page, end_page, and category to uniquely identify the grouping
        data = f"{doc.start_page}:{doc.end_page}:{doc.category}"
        hasher.update(data.encode("utf-8"))
    return hasher.hexdigest()

@pytest.fixture
def mock_llm_client():
    with patch("src.processing.pipeline.LLMClient") as mock:
        yield mock.return_value

@pytest.fixture
def pipeline(mock_llm_client):
    return Pipeline(api_key="test_key")

@pytest.fixture
def sample_pages():
    return [
        (0, PageData(category="cat1", canonical_tenant="tenant1")),
        (1, PageData(category="cat1", canonical_tenant="tenant1")),
        (2, PageData(category="cat2", canonical_tenant="tenant2")),
    ]

def test_routing_checkpointing_and_resumption(tmp_path, pipeline, sample_pages):
    """Verify that routing is checkpointed and can be resumed."""
    checkpoint_path = str(tmp_path / "run_checkpoint.json")
    
    # Mock route_document to just return a dummy folder
    with patch("src.processing.routing.route_document") as mock_route:
        mock_route.return_value = ("folder/path", False)
        
        # Mock process_with_shrink to avoid actual LLM calls
        with patch("src.processing.grouping.process_with_shrink") as mock_group:
            mock_group.side_effect = [
                [
                    DocumentGroup(start_page=0, end_page=0, category="cat1", primary_tenant="tenant1", dates=[], canonical_tenant="tenant1"),
                    DocumentGroup(start_page=1, end_page=1, category="cat1", primary_tenant="tenant1", dates=[], canonical_tenant="tenant1"),
                ],
                [
                    DocumentGroup(start_page=2, end_page=2, category="cat2", primary_tenant="tenant2", dates=[], canonical_tenant="tenant2"),
                ]
            ]

            # 1. Run once, but simulate an interruption after the first document
            mock_route.side_effect = [
                ("folder/1", False),
                Exception("Simulated interruption"),
            ]
            
            try:
                pipeline._group_and_route_documents(sample_pages, run_checkpoint_path=checkpoint_path)
            except Exception as e:
                assert str(e) == "Simulated interruption"
            
            routing_checkpoint = checkpoint_path.replace(".json", "_routing.json")
            assert os.path.exists(routing_checkpoint)
            
            with open(routing_checkpoint, "r") as f:
                state_data = json.load(f)
                assert state_data["processed_indices"] == [0]
            
            # 2. Resume routing
            mock_route.side_effect = None
            mock_route.return_value = ("folder/resumed", False)
            
            pipeline._group_and_route_documents(sample_pages, run_checkpoint_path=checkpoint_path)
            
            # First document skipped, total calls: 2 (interrupted: 1 ok, 1 fail) + 2 (resumed: 2 ok) = 4
            assert mock_route.call_count == 4
            assert not os.path.exists(routing_checkpoint)

def test_routing_sanity_check_checksum_mismatch(tmp_path, pipeline, sample_pages):
    """Verify that routing restarts if grouping checksum changes."""
    checkpoint_path = str(tmp_path / "run_checkpoint.json")
    routing_checkpoint = checkpoint_path.replace(".json", "_routing.json")
    
    # 1. Setup a routing checkpoint with a different checksum
    state = RoutingState(processed_indices=[0], grouping_checksum="wrong_checksum")
    with open(routing_checkpoint, "w") as f:
        f.write(state.model_dump_json())
        
    with patch("src.processing.routing.route_document") as mock_route:
        mock_route.return_value = ("folder/path", False)
        
        with patch("src.processing.grouping.process_with_shrink") as mock_group:
            mock_group.side_effect = [
                [
                    DocumentGroup(start_page=0, end_page=0, category="cat1", primary_tenant="tenant1", dates=[], canonical_tenant="tenant1"),
                    DocumentGroup(start_page=1, end_page=1, category="cat1", primary_tenant="tenant1", dates=[], canonical_tenant="tenant1"),
                ],
                [
                    DocumentGroup(start_page=2, end_page=2, category="cat2", primary_tenant="tenant2", dates=[], canonical_tenant="tenant2"),
                ]
            ]
            
            pipeline._group_and_route_documents(sample_pages, run_checkpoint_path=checkpoint_path)
            
            # Checksum mismatch -> route all 3
            assert mock_route.call_count == 3
            assert not os.path.exists(routing_checkpoint)
