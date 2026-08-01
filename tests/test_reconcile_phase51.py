import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.reconcile.core import run_reconcile_mode
from src.utils.fs import create_shortcut

class DummyArgs:
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.dry_run = False

def test_phase51_multipage_pdf(tmp_path):
    house_id = "510"
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [
        {"name": "Tenant", "start_date": "2021-01-01", "end_date": "present"}
    ]
    with open(source_dir / f"{house_id}_tenants.yaml", "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [],
        "grouped_documents": [],
        "manifest": {"per_page": []}
    }
    with open(source_dir / f"{house_id}_state.json", "w", encoding="utf-8") as f:
        json.dump(state_data, f)
        
    # Raw PDF
    subfolder = target_dir / "Category"
    subfolder.mkdir(parents=True)
    raw_pdf = subfolder / "2023-05-15 - Raw Invoice.pdf"
    raw_pdf.touch()
    
    # Ghost Shortcut
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)
    vault_pdf = vault_dir / "doc_mockvault123.pdf"
    vault_pdf.touch()
    
    ghost_subfolder = target_dir / "GhostFolder"
    ghost_subfolder.mkdir(parents=True)
    shortcut_path = ghost_subfolder / "2022-11-20 - Ghost Doc.lnk"
    create_shortcut(str(vault_pdf.resolve()), str(shortcut_path.resolve()))
    
    args = DummyArgs(target_dir=target_dir)
    
    # Mock pypdf and FileOrganizer
    with patch("src.reconcile.core.FileOrganizer") as mock_org, \
         patch("src.reconcile.core.pypdf.PdfReader") as mock_pdf:
         
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Tenant": "Tenant"}, "Tenant")
        
        # Mock PdfReader to return 3 pages
        mock_reader = MagicMock()
        mock_reader.pages = [1, 2, 3]
        mock_pdf.return_value = mock_reader
        
        result = run_reconcile_mode(args)
        
    assert result == 0
    
    # Check state
    new_source_dir = tmp_path / f"{house_id} - Tenant" / ".source_files"
    with open(new_source_dir / f"{house_id}_state.json", "r", encoding="utf-8") as f:
        new_state = json.load(f)
        
    pages = new_state.get("cleaned_pages", [])
    groups = new_state.get("grouped_documents", [])
    
    # We expect 3 pages for ghost shortcut and 3 pages for raw PDF = 6 pages total
    assert len(pages) == 6
    assert len(groups) == 2
    
    assert groups[0].get("end_page") - groups[0].get("start_page") == 2
    assert groups[1].get("end_page") - groups[1].get("start_page") == 2
