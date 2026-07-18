from typing import Any
import pytest
import logging
import os
import json
from unittest.mock import MagicMock, patch
from src.grouping.utils import verify_groups, merge_chunks
from src.grouping.core import process_with_shrink, _process_chunk
from src.grouping.config import FORM_PROMPT, LETTER_PROMPT, OTHER_PROMPT
from src.grouping.state import GroupingState, GroupingStateManager
from src.core.exceptions import ProviderRotationExhaustedError, GracefulHaltException
from src.core.schemas import GroupEntry, DocumentGroup, GroupingResponse
from types import SimpleNamespace

logger = logging.getLogger(f"file_organizer.{__name__}")

logger = logging.getLogger(f"file_organizer.{__name__}")

class MockPage:
    def __init__(self, index, category, tenant="Test Tenant", date="2023-01-01", content_explanation="Some content", subject="Some subject") -> Any:
        """
        Provide the   init   fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        self.original_index = index
        self.category = category
        self.canonical_tenant = tenant
        self.resolved_date = date
        self.date = date
        self.content_explanation = content_explanation
        self.subject = subject

# --- Utils Tests ---

def test_verification_logic() -> None:
    """
    Test verification logic.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
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

def test_overlap_merge() -> None:
    """
    Test overlap merge.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
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

def test_anchor_page_merging() -> None:
    """
    Test anchor page merging.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    # overlap_page_idx = 9
    
    # Scenario A: Continuation (MERGE)
    chunk1_a = [DocumentGroup(start_page=6, end_page=9, primary_tenant="T1", category="forms", dates=[])]
    chunk2_a = [DocumentGroup(start_page=9, end_page=12, primary_tenant="T1", category="forms", dates=[])]
    merged_a = merge_chunks(chunk1_a, chunk2_a, 9)
    assert len(merged_a) == 1
    assert merged_a[0].start_page == 6
    assert merged_a[0].end_page == 12

    # Scenario B: End of Doc 1 and Start of Doc 2 (SPLIT)
    chunk1_b = [
        DocumentGroup(start_page=6, end_page=8, primary_tenant="T1", category="forms", dates=[]),
        DocumentGroup(start_page=9, end_page=9, primary_tenant="T1", category="forms", dates=[])
    ]
    chunk2_b = [
        DocumentGroup(start_page=9, end_page=9, primary_tenant="T1", category="forms", dates=[]),
        DocumentGroup(start_page=10, end_page=12, primary_tenant="T1", category="forms", dates=[])
    ]
    merged_b = merge_chunks(chunk1_b, chunk2_b, 9)
    assert len(merged_b) == 3
    assert merged_b[0].end_page == 8
    assert merged_b[1].start_page == 9 and merged_b[1].end_page == 9
    assert merged_b[2].start_page == 10

    # Scenario C: Fragment / Not a continuing document (SPLIT)
    chunk1_c = [DocumentGroup(start_page=6, end_page=9, primary_tenant="T1", category="forms", dates=[])]
    chunk2_c = [
        DocumentGroup(start_page=9, end_page=9, primary_tenant="T1", category="forms", dates=[]),
        DocumentGroup(start_page=10, end_page=12, primary_tenant="T1", category="forms", dates=[])
    ]
    merged_c = merge_chunks(chunk1_c, chunk2_c, 9)
    assert len(merged_c) == 3
    assert merged_c[0].end_page == 8 # Trust Chunk 2 for page 9, so Chunk 1 ends at 8
    assert merged_c[1].start_page == 9 and merged_c[1].end_page == 9

    # Scenario D: Conflict on Anchor Page decisions (SPLIT)
    chunk1_d = [
        DocumentGroup(start_page=6, end_page=8, primary_tenant="T1", category="forms", dates=[]),
        DocumentGroup(start_page=9, end_page=9, primary_tenant="T1", category="forms", dates=[])
    ]
    chunk2_d = [DocumentGroup(start_page=9, end_page=12, primary_tenant="T1", category="forms", dates=[])]
    merged_d = merge_chunks(chunk1_d, chunk2_d, 9)
    assert len(merged_d) == 2
    assert merged_d[0].end_page == 8
    assert merged_d[1].start_page == 9


# --- Core Unit Tests ---

def test_process_chunk_metadata_extraction() -> None:
    """
    Test process chunk metadata extraction.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    pages = [
        MockPage(index=100, category="forms", tenant="Tenant A", date="2023-05-01"),
        MockPage(index=101, category="forms", tenant="Tenant A", date="2023-05-02"),
    ]
    llm_client = MagicMock()
    llm_client.generate_content.return_value = GroupingResponse(
        groups=[GroupEntry(start_page=0, end_page=1, reason="Grouped", brief_arabic_title="Title")]
    )
    
    groups = _process_chunk(pages, 0, 2, llm_client, FORM_PROMPT)
    
    assert len(groups) == 1
    g = groups[0]
    assert g.start_page == 100
    assert g.end_page == 101
    assert g.primary_tenant == "Tenant A"
    assert g.category == "forms"
    assert "2023-05-01" in g.dates
    assert "2023-05-02" in g.dates
    assert g.reason == "Grouped"

def test_process_with_shrink_deterministic_bypasses() -> None:
    """
    Test process with shrink deterministic bypasses.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    llm_client = MagicMock()
    
    # Contract: 1 group
    pages_contract = [MockPage(0, "contract"), MockPage(1, "contract")]
    groups_contract = process_with_shrink(pages_contract, llm_client)
    assert len(groups_contract) == 1
    assert groups_contract[0].start_page == 0
    assert groups_contract[0].end_page == 1
    
    # ID Cards: 1 group
    pages_id = [MockPage(0, "id_cards"), MockPage(1, "id_cards")]
    groups_id = process_with_shrink(pages_id, llm_client)
    assert len(groups_id) == 1
    assert groups_id[0].start_page == 0
    assert groups_id[0].end_page == 1

    # Utility Bills: 1 group per page
    pages_bills = [MockPage(0, "utility_bills"), MockPage(1, "utility_bills")]
    groups_bills = process_with_shrink(pages_bills, llm_client)
    assert len(groups_bills) == 2
    assert groups_bills[0].start_page == 0 and groups_bills[0].end_page == 0
    assert groups_bills[1].start_page == 1 and groups_bills[1].end_page == 1
    
    llm_client.generate_content.assert_not_called()

def test_process_with_shrink_default_routing() -> None:
    """
    Test process with shrink default routing.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    llm_client = MagicMock()
    llm_client.generate_content.return_value = GroupingResponse(
        groups=[GroupEntry(start_page=0, end_page=0, reason="R", brief_arabic_title="T")]
    )
    
    # "unknown" category should route to FORM_PROMPT
    pages = [MockPage(0, "unknown")]
    process_with_shrink(pages, llm_client)
    
    # Verify prompt used in generate_content call
    args, kwargs = llm_client.generate_content.call_args
    prompt = kwargs['contents'][0] if 'contents' in kwargs else args[0][0]
    assert FORM_PROMPT in prompt

def test_resilient_loop_success(tmp_path) -> None:
    """
    Test resilient loop success.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    state_file = tmp_path / "success.state.json"
    manager = GroupingStateManager(str(state_file))
    llm_client = MagicMock()
    
    def llm_side_effect(contents, **kwargs) -> Any:
        """
        Provide the llm side effect fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        prompt = contents[0]
        if "Page 0 to Page 3" in prompt:
            return GroupingResponse(groups=[GroupEntry(start_page=0, end_page=3, reason="R", brief_arabic_title="T")])
        if "Page 3 to Page 6" in prompt:
            return GroupingResponse(groups=[GroupEntry(start_page=3, end_page=6, reason="R", brief_arabic_title="T")])
        if "Page 6 to Page 9" in prompt:
            return GroupingResponse(groups=[GroupEntry(start_page=6, end_page=9, reason="R", brief_arabic_title="T")])
        return GroupingResponse(groups=[])

    llm_client.generate_content.side_effect = llm_side_effect
    
    pages = [MockPage(i, "forms") for i in range(10)]
    groups = process_with_shrink(pages, llm_client, state_manager=manager)
    
    assert len(groups) > 0
    state = manager.load_state()
    assert state.chunk_size_index == 0

def test_resilient_loop_shrink(tmp_path) -> None:
    """
    Test resilient loop shrink.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    state_file = tmp_path / "shrink.state.json"
    manager = GroupingStateManager(str(state_file))
    llm_client = MagicMock()
    
    def llm_side_effect(contents, **kwargs) -> Any:
        """
        Provide the llm side effect fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        prompt = contents[0]
        # Extract range from prompt: "Page X to Page Y"
        import re
        match = re.search(r"Page (\d+) to Page (\d+)", prompt)
        if not match:
            return GroupingResponse(groups=[])
        
        start = int(match.group(1))
        end = int(match.group(2))
        
        # Force shrink at the beginning (size 4)
        if start == 0 and (end == 3): # Size 4
            raise ProviderRotationExhaustedError("Rotation failed")
            
        return GroupingResponse(groups=[GroupEntry(start_page=start, end_page=end, reason="R", brief_arabic_title="T")])

    llm_client.generate_content.side_effect = llm_side_effect
    
    pages = [MockPage(i, "forms") for i in range(10)]
    groups = process_with_shrink(pages, llm_client, state_manager=manager)
    
    assert len(groups) > 0
    # Verify shrink happened after 1 failure
    calls = llm_client.generate_content.call_args_list
    first_prompt = calls[0].args[0][0] if calls[0].args else calls[0].kwargs['contents'][0]
    second_prompt = calls[1].args[0][0] if calls[1].args else calls[1].kwargs['contents'][0]
    assert "Page 0 to Page 3" in first_prompt
    assert "Page 0 to Page 2" in second_prompt

def test_resilient_loop_halt(tmp_path) -> None:
    """
    Test resilient loop halt.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    state_file = tmp_path / "halt.state.json"
    manager = GroupingStateManager(str(state_file))
    llm_client = MagicMock()
    
    llm_client.generate_content.side_effect = ProviderRotationExhaustedError("Rotation failed")
    
    pages = [MockPage(i, "forms") for i in range(10)]
    
    with pytest.raises(GracefulHaltException):
        process_with_shrink(pages, llm_client, state_manager=manager)
    
    state = manager.load_state()
    assert state.chunk_size_index == 2
    assert state.current_page_index == 0

def test_resilient_loop_resume(tmp_path) -> None:
    """
    Test resilient loop resume.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    state_file = tmp_path / "resume.state.json"
    manager = GroupingStateManager(str(state_file))
    
    initial_state = GroupingState(
        current_page_index=5,
        chunk_size_index=1,
        failure_count=1,
        processed_groups=[{"start_page": 0, "end_page": 4, "primary_tenant": "T1", "category": "forms", "dates": [], "reason": "R", "brief_arabic_title": "T"}]
    )
    manager.save_state(initial_state)
    
    llm_client = MagicMock()
    
    def llm_side_effect(contents, **kwargs) -> Any:
        """
        Provide the llm side effect fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        prompt = contents[0]
        if "Page 5 to Page 7" in prompt:
            return GroupingResponse(groups=[GroupEntry(start_page=5, end_page=7, reason="R", brief_arabic_title="T")])
        if "Page 7 to Page 9" in prompt:
            return GroupingResponse(groups=[GroupEntry(start_page=7, end_page=9, reason="R", brief_arabic_title="T")])
        return GroupingResponse(groups=[])

    llm_client.generate_content.side_effect = llm_side_effect
    
    pages = [MockPage(i, "forms") for i in range(10)]
    groups = process_with_shrink(pages, llm_client, state_manager=manager)
    
    assert len(groups) >= 2
    assert groups[0].start_page == 0 and groups[0].end_page == 4
    # After resume, 5-7 and 7-9 are merged because they share page 7 and same metadata
    assert groups[1].start_page == 5 and groups[1].end_page == 9

def test_resilient_loop_partial_success(tmp_path) -> None:
    """
    Test resilient loop partial success.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    state_file = tmp_path / "partial.state.json"
    manager = GroupingStateManager(str(state_file))
    llm_client = MagicMock()
    
    def llm_side_effect(contents, **kwargs) -> Any:
        """
        Provide the llm side effect fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        prompt = contents[0]
        if "Page 0 to Page 3" in prompt:
            return GroupingResponse(groups=[GroupEntry(start_page=0, end_page=3, reason="R", brief_arabic_title="T")])
        if "Page 3 to Page 6" in prompt:
            return GroupingResponse(groups=[GroupEntry(start_page=3, end_page=6, reason="R", brief_arabic_title="T")])
        if "Page 6 to Page 9" in prompt:
            return GroupingResponse(groups=[GroupEntry(start_page=6, end_page=9, reason="R", brief_arabic_title="T")])
        return GroupingResponse(groups=[])

    llm_client.generate_content.side_effect = llm_side_effect
    
    pages = [MockPage(i, "forms") for i in range(10)]
    process_with_shrink(pages, llm_client, state_manager=manager)
    
    state = manager.load_state()
    assert state.chunk_size_index == 0

@patch("src.utils.logger.log_decision_trace")
def test_process_with_shrink_telemetry(mock_log) -> None:
    """
    Test process with shrink telemetry.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    llm_client = MagicMock()
    llm_client.generate_content.return_value = GroupingResponse(
        groups=[GroupEntry(start_page=0, end_page=0, reason="R", brief_arabic_title="T")]
    )
    
    pages = [MockPage(0, "forms")]
    process_with_shrink(pages, llm_client)
    
    mock_log.assert_called_once()
    args = mock_log.call_args[0]
    assert args[0] == "grouping"
    assert "final_groups" in args[1]

def test_grouping_e2e_scenario() -> None:
    """
    Test grouping e2e scenario.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    llm_client = MagicMock()
    
    # Scenario: Pages 0-2 are a letter (1 group), Pages 3-4 are a form (2 groups)
    # We'll need a side_effect for generate_content to return different things
    def llm_side_effect(contents, **kwargs) -> Any:
        """
        Provide the llm side effect fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        prompt = contents[0]
        if "Page 0 to Page 3" in prompt or "Page 0 to Page 2" in prompt:
            # First chunk (0-3). Must end at 3.
            return GroupingResponse(groups=[
                GroupEntry(start_page=0, end_page=2, reason="Letter", brief_arabic_title="L"),
                GroupEntry(start_page=3, end_page=3, reason="Forms", brief_arabic_title="F")
            ])
        if "Page 3 to Page 4" in prompt:
            # Overlap chunk.
            return GroupingResponse(groups=[
                GroupEntry(start_page=3, end_page=4, reason="Forms", brief_arabic_title="F")
            ])
        return GroupingResponse(groups=[])

    llm_client.generate_content.side_effect = llm_side_effect
    
    # 5 pages total. 0-2 letters, 3-4 forms.
    # But process_with_shrink takes category from pages[0].
    # If we want mixed categories, we'd need to use category_presplit first,
    # but process_with_shrink assumes a single category for the whole list.
    # Let's test it with one category "forms" and see how it groups.

    pages = [MockPage(i, "forms") for i in range(5)]
    groups = process_with_shrink(pages, llm_client)

    assert len(groups) == 2
    assert groups[0].start_page == 0 and groups[0].end_page == 2
    assert groups[1].start_page == 3 and groups[1].end_page == 4

def test_boundary_signals() -> None:
    """
    Test boundary signals.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    assert "subject/content shift" in FORM_PROMPT
    assert "DO NOT split on date changes" in FORM_PROMPT

# --- State Manager Tests ---

def test_grouping_state_persistence(tmp_path) -> None:
    """
    Test grouping state persistence.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    state_file = tmp_path / "grouping.state.json"
    manager = GroupingStateManager(str(state_file))
    
    # Initial load should be default
    state = manager.load_state()
    assert state.current_page_index == 0
    assert state.failure_count == 0
    
    # Save modified state
    new_state = GroupingState(
        current_page_index=10,
        chunk_size_index=2,
        failure_count=5,
        processed_groups=[{"start": 0, "end": 9}]
    )
    manager.save_state(new_state)
    
    # Load and verify
    loaded_state = manager.load_state()
    assert loaded_state.current_page_index == 10
    assert loaded_state.chunk_size_index == 2
    assert loaded_state.failure_count == 5
    assert loaded_state.processed_groups == [{"start": 0, "end": 9}]

def test_grouping_state_corrupted_fallback(tmp_path) -> None:
    """
    Test grouping state corrupted fallback.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    state_file = tmp_path / "grouping.state.json"
    manager = GroupingStateManager(str(state_file))
    
    # 1. Create a valid state and save it twice to ensure a backup exists
    valid_state = GroupingState(current_page_index=5)
    manager.save_state(valid_state)
    # Second save creates the .bak of the first save
    manager.save_state(valid_state)
    
    # 2. Corrupt the main state file
    with open(state_file, "w", encoding="utf-8") as f:
        f.write("NOT JSON")
    
    # 3. Load state - should fallback to .bak
    loaded_state = manager.load_state()
    assert loaded_state.current_page_index == 5

def test_grouping_state_missing_files() -> None:
    """
    Test grouping state missing files.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    # Manager with non-existent files should return default state
    manager = GroupingStateManager("non_existent_file.json")
    state = manager.load_state()
    assert isinstance(state, GroupingState)
    assert state.current_page_index == 0

def test_grouping_state_atomic_write_simulation(tmp_path) -> None:
    """
    Test grouping state atomic write simulation.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    state_file = tmp_path / "grouping.state.json"
    manager = GroupingStateManager(str(state_file))
    
    # Save initial state
    initial_state = GroupingState(current_page_index=1)
    manager.save_state(initial_state)
    
    # Simulate a crash during save_state by mocking os.replace to fail
    # We want to ensure the original state_file is untouched if replace fails
    with patch("os.replace", side_effect=OSError("Disk full")):
        try:
            manager.save_state(GroupingState(current_page_index=2))
        except OSError:
            pass
    
    # Original state should still be loadable
    loaded_state = manager.load_state()
    assert loaded_state.current_page_index == 1
