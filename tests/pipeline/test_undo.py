import pytest
import os
import json
import fitz
from pathlib import Path
from src.pipeline.undo import run_undo
import shutil

@pytest.fixture
def mock_target_dir(tmp_path):
    target_dir = tmp_path / "12345 - Test House"
    target_dir.mkdir()
    
    # Create fake folders
    (target_dir / "Tenant_A").mkdir()
    (target_dir / "[Timeline View]").mkdir()
    
    source_files = target_dir / ".source_files"
    source_files.mkdir()
    
    vault = source_files / "vault"
    vault.mkdir()
    
    # Create fake vault PDFs
    for vault_id in ["v1", "v2"]:
        pdf = fitz.open()
        pdf.new_page()
        pdf.save(str(vault / f"doc_{vault_id}.pdf"))
        pdf.close()
        
    state_file = source_files / "12345_state.json"
    state_data = {
        "routed_documents": [
            {"start_page": 1, "end_page": 1, "vault_id": "v2"},
            {"start_page": 0, "end_page": 0, "vault_id": "v1"}
        ]
    }
    with open(state_file, "w") as f:
        json.dump(state_data, f)
        
    return target_dir

def test_run_undo_success(mock_target_dir):
    result = run_undo(mock_target_dir)
    assert result == 0
    
    output_pdf = mock_target_dir / "12345.pdf"
    assert output_pdf.exists()
    
    # Check page count
    with fitz.open(str(output_pdf)) as doc:
        assert doc.page_count == 2
        
    # Check folders wiped out
    assert not (mock_target_dir / "Tenant_A").exists()
    assert not (mock_target_dir / "[Timeline View]").exists()
    assert not (mock_target_dir / ".source_files").exists()
    
def test_run_undo_missing_state(tmp_path):
    target_dir = tmp_path / "12345 - Test"
    target_dir.mkdir()
    
    result = run_undo(target_dir)
    assert result == 1
    
def test_run_undo_missing_vault(mock_target_dir):
    vault_file = mock_target_dir / ".source_files" / "vault" / "doc_v1.pdf"
    vault_file.unlink()
    
    result = run_undo(mock_target_dir)
    assert result == 1
