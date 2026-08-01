import os
import sys
import builtins
from pathlib import Path
import pytest

from src.reconcile.core import run_reconcile_mode

def test_preflight_lock_detection_aborts_cleanly(tmp_path, monkeypatch, capsys):
    house_dir = tmp_path / "101 - Test House"
    house_dir.mkdir()
    source_dir = house_dir / ".source_files"
    source_dir.mkdir()
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    
    test_pdf = vault_dir / "doc_12345.pdf"
    test_pdf.write_text("dummy pdf content")
    
    yaml_file = source_dir / "101_tenants.yaml"
    yaml_file.write_text("- name: Tenant A\n  start_date: '2020-01-01'\n  end_date: '2021-01-01'")
    
    state_file = source_dir / "101_state.json"
    state_file.write_text("{}")
    
    class Args:
        target_dir = house_dir
        dry_run = False
        
    args = Args()
    
    original_open = builtins.open
    
    def mocked_open(*o_args, **kwargs):
        # Block our test pdf in append mode to simulate lock
        if str(o_args[0]) == str(test_pdf) and len(o_args) > 1 and o_args[1] == 'a':
            raise PermissionError("Simulated lock from another process")
        return original_open(*o_args, **kwargs)
        
    monkeypatch.setattr(builtins, "open", mocked_open)
    
    with pytest.raises(SystemExit) as exc_info:
        run_reconcile_mode(args)
        
    assert exc_info.value.code == 1
    
    captured = capsys.readouterr()
    assert "ABORTED: The following file is currently locked by another process or user:" in captured.out
    assert str(test_pdf) in captured.out
    
    # Verify no state or files were modified
    assert state_file.read_text() == "{}"
    assert test_pdf.read_text() == "dummy pdf content"
