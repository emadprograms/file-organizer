import os
import tempfile
from pathlib import Path
import pytest

from src.fs_ui.lock import acquire_lock, release_lock, LockExistsError

@pytest.fixture
def lock_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir) / "test.lock"

def test_acquire_lock_success(lock_path):
    """Test 1: `acquire_lock` successfully writes the current PID to a new lockfile."""
    acquire_lock(lock_path)
    assert lock_path.exists()
    assert lock_path.read_text().strip() == str(os.getpid())

def test_acquire_lock_raises_if_alive(lock_path, monkeypatch):
    """Test 2: `acquire_lock` raises `LockExistsError` if the lockfile contains a PID that is currently alive."""
    # Write a dummy PID
    dummy_pid = 999999
    lock_path.write_text(str(dummy_pid))
    
    # Mock os.kill to not raise OSError (simulate alive)
    monkeypatch.setattr(os, "kill", lambda pid, sig: None)
    
    with pytest.raises(LockExistsError):
        acquire_lock(lock_path)

def test_acquire_lock_overwrites_if_dead(lock_path, monkeypatch):
    """Test 3: `acquire_lock` silently overwrites the lockfile if it contains a PID that is no longer alive."""
    dummy_pid = 999999
    lock_path.write_text(str(dummy_pid))
    
    # Mock os.kill to raise OSError (simulate dead)
    def mock_kill(pid, sig):
        raise ProcessLookupError()
    monkeypatch.setattr(os, "kill", mock_kill)
    
    acquire_lock(lock_path)
    assert lock_path.read_text().strip() == str(os.getpid())

def test_release_lock_success(lock_path):
    """Test 4: `release_lock` removes the lockfile only if it exists and matches the current PID."""
    lock_path.write_text(str(os.getpid()))
    release_lock(lock_path)
    assert not lock_path.exists()

def test_release_lock_ignores_other_pid(lock_path):
    """Test 4 part 2: `release_lock` does not remove the lockfile if it matches a different PID."""
    lock_path.write_text("999999")
    release_lock(lock_path)
    assert lock_path.exists()
    assert lock_path.read_text().strip() == "999999"

def test_release_lock_ignores_missing(lock_path):
    """Test 4 part 3: `release_lock` ignores missing lockfiles silently."""
    release_lock(lock_path)  # Should not raise
    assert not lock_path.exists()
