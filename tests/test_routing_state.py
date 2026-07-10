import pytest
import os
import json
from src.processing.routing.state import RoutingState, RoutingStateManager

def test_routing_state_manager_save_load(tmp_path):
    """Test that RoutingState is correctly saved and loaded."""
    state_file = str(tmp_path / "routing_state.json")
    manager = RoutingStateManager(state_file)
    
    initial_state = RoutingState(processed_indices=[1, 2, 3], grouping_checksum="abc-123")
    manager.save_state(initial_state)
    
    loaded_state = manager.load_state()
    assert loaded_state.processed_indices == [1, 2, 3]
    assert loaded_state.grouping_checksum == "abc-123"

def test_routing_state_manager_atomic_backup(tmp_path):
    """Test that a backup is created and used if the main file is corrupted."""
    state_file = str(tmp_path / "routing_state.json")
    manager = RoutingStateManager(state_file)
    
    # 1. Save first state
    state1 = RoutingState(processed_indices=[1], grouping_checksum="sum1")
    manager.save_state(state1)
    
    # 2. Save second state (this should create a backup of state1)
    state2 = RoutingState(processed_indices=[1, 2], grouping_checksum="sum2")
    manager.save_state(state2)
    
    # 3. Corrupt the main state file
    with open(state_file, "w", encoding="utf-8") as f:
        f.write("CORRUPTED JSON")
        
    # 4. Load state - should fallback to backup (state2's backup is state1?)
    # Wait, the logic is:
    # save_state(state2):
    #   copy state_file (state1) -> bak_file
    #   replace tmp (state2) -> state_file
    # So bak_file contains state1.
    
    loaded_state = manager.load_state()
    assert loaded_state.processed_indices == [1]
    assert loaded_state.grouping_checksum == "sum1"

def test_routing_state_manager_default_state(tmp_path):
    """Test that load_state returns a default state if no files exist."""
    state_file = str(tmp_path / "non_existent.json")
    manager = RoutingStateManager(state_file)
    
    loaded_state = manager.load_state()
    assert loaded_state.processed_indices == []
    assert loaded_state.grouping_checksum == ""
