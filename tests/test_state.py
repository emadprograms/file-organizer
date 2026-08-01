import pytest
import json
from pathlib import Path
from src.core.state import State
from src.utils.fs import atomic_write

def test_state_schema_initialization(tmp_path):
    """STATE-01: Define state.json schema to encompass all previous pipeline states."""
    house_id = "test_house_123"
    state_dir = tmp_path / "states"
    state_dir.mkdir()
    
    state = State(house_id, state_dir)
    assert state.data["house_id"] == house_id
    assert "cleaned_pages" in state.data
    assert "grouped_documents" in state.data
    assert "routed_documents" in state.data
    assert state.state_file == state_dir / f"{house_id}_state.json"

def test_state_atomic_save(tmp_path, monkeypatch):
    """STATE-04: Maintain crash-safe atomic writes for state.json."""
    house_id = "test_house_atomic"
    state_dir = tmp_path / "states"
    
    state = State(house_id, state_dir)
    state.data["cleaned_pages"] = [{"page": 1}]
    
    # Track if atomic_write was used
    atomic_used = False
    original_atomic = atomic_write
    
    import contextlib
    
    @contextlib.contextmanager
    def mock_atomic_write(filepath):
        nonlocal atomic_used
        atomic_used = True
        with original_atomic(filepath) as tmp:
            yield tmp
            
    import src.core.state
    monkeypatch.setattr(src.core.state, "atomic_write", mock_atomic_write)
    
    state.save()
    
    assert atomic_used
    assert state.state_file.exists()
    
    with open(state.state_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["cleaned_pages"] == [{"page": 1}]

def test_state_loads_existing_data(tmp_path):
    """Test State loads from an existing state.json file."""
    house_id = "test_house_load"
    state_dir = tmp_path / "states"
    state_dir.mkdir()
    
    state_file = state_dir / f"{house_id}_state.json"
    initial_data = {
        "house_id": house_id,
        "cleaned_pages": [{"index": 1}],
        "grouped_documents": [{"id": 1}],
        "routed_documents": None,
    }
    state_file.write_text(json.dumps(initial_data))
    
    state = State(house_id, state_dir)
    
    assert state.data["cleaned_pages"] == [{"index": 1}]
    assert state.data["grouped_documents"] == [{"id": 1}]
    assert state.data["routed_documents"] is None

def test_state_auto_migrates_shortcut_name(tmp_path):
    """Test auto-migrating shortcut_name to shortcuts."""
    house_id = "test_house_mig"
    state_dir = tmp_path / "states"
    state_dir.mkdir()
    
    state_file = state_dir / f"{house_id}_state.json"
    initial_data = {
        "house_id": house_id,
        "grouped_documents": [
            {"id": 1, "shortcut_name": "old_shortcut"},
            {"id": 2}
        ]
    }
    state_file.write_text(json.dumps(initial_data))
    
    state = State(house_id, state_dir)
    assert state.data["grouped_documents"][0]["shortcuts"] == ["old_shortcut"]
    assert "shortcut_name" not in state.data["grouped_documents"][0]
    assert state.data["grouped_documents"][1]["shortcuts"] == []
