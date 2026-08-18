import pytest
from pathlib import Path
import json
import shutil
import fitz
from src.pipeline.undo import run_undo

def test_undo_uses_trash(tmp_path):
    house_id = "888"
    target_dir = tmp_path / f"{house_id} - Undo Test"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)
    
    # Create mock state.json
    state_data = {
        "house_id": house_id,
        "routed_documents": [
            {
                "start_page": 0,
                "end_page": 0,
                "vault_id": "v1"
            }
        ]
    }
    with open(source_dir / f"{house_id}_state.json", "w", encoding='utf-8') as f:
        json.dump(state_data, f)
        
    # Create mock vault PDF
    import fitz
    pdf = fitz.open()
    pdf.new_page()
    pdf.save(str(vault_dir / "doc_v1.pdf"))
    pdf.close()
    
    # Create some dummy folders and files in target_dir to see if they are moved to .trash
    dummy_file = target_dir / "dummy_shortcut.lnk"
    with open(dummy_file, "w") as f:
        f.write("dummy")
        
    dummy_dir = target_dir / "Tenant Folder"
    dummy_dir.mkdir()
    
    # Run undo
    result = run_undo(target_dir)
    assert result == 0
    
    # Check that reconstructed PDF exists
    assert (target_dir / f"{house_id}.pdf").exists()
    
    # Check that .trash exists
    trash_dir = target_dir / ".trash"
    assert trash_dir.exists()
    
    # Check that dummy file and dir are moved to .trash with timestamps
    trashed_items = list(trash_dir.iterdir())
    assert len(trashed_items) >= 2
    
    dummy_file_trashed = False
    dummy_dir_trashed = False
    
    for item in trashed_items:
        if item.name.startswith("dummy_shortcut.lnk_"):
            dummy_file_trashed = True
        if item.name.startswith("Tenant Folder_"):
            dummy_dir_trashed = True
            
    assert dummy_file_trashed
    assert dummy_dir_trashed
    
    # And .source_files might have some preserved files (like tenants.yaml), but state.json is destroyed
    assert not (target_dir / ".source_files" / f"{house_id}_state.json").exists()
