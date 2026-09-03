import pytest
from pathlib import Path
import json
import yaml
import os
import shutil

from src.reconcile.core import run_reconcile_mode
from src.utils.fs import create_shortcut

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"

def test_reconcile_unassigned_bug(tmp_path):
    # Setup mock house structure
    house_id = "556"
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [
        {"name": "Test Tenant", "start_date": "2021-01-01", "end_date": "2025-01-01"}
    ]
    with open(source_dir / f"{house_id}_tenants.yaml", "w", encoding='utf-8') as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [],
        "grouped_documents": [],
        "manifest": {
            "per_page": []
        }
    }
    with open(source_dir / f"{house_id}_state.json", "w", encoding='utf-8') as f:
        json.dump(state_data, f)
        
    # Create a raw PDF in a canonical folder
    canonical_folder = "Test Tenant \u200e(2021 - 2025)\u200e"
    raw_pdf_path = target_dir / canonical_folder / "2021-01-01 - Raw Document.pdf"
    raw_pdf_path.parent.mkdir(parents=True)
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(raw_pdf_path, "wb") as f:
        writer.write(f)
        
    # Also create a ghost shortcut scenario in the canonical folder
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)
    ghost_vault_pdf = vault_dir / "doc_GHOST123.pdf"
    with open(ghost_vault_pdf, "wb") as f:
        writer.write(f)
        
    ghost_lnk_path = target_dir / canonical_folder / "01_Ghost" / "2021-01-02 - Ghost Doc.lnk"
    ghost_lnk_path.parent.mkdir(parents=True)
    create_shortcut(str(ghost_vault_pdf.resolve()), str(ghost_lnk_path.resolve()))
    
    args = DummyArgs(target_dir=target_dir)
    
    # Run 1: Normal processing
    result1 = run_reconcile_mode(args)
    assert result1 == 0
    
    # Check state.json
    new_target_dir = target_dir
    for candidate in target_dir.parent.iterdir():
        if candidate.is_dir() and (candidate / ".source_files").exists():
            new_target_dir = candidate
            break
            
    source_dir = new_target_dir / ".source_files"
    
    with open(source_dir / f"{house_id}_state.json", "r", encoding='utf-8') as f:
        new_state = json.load(f)
        
    pages = new_state.get("cleaned_pages", [])
    assert len(pages) == 2
    
    for p in pages:
        assert getattr(p, "canonical_tenant", p.get("canonical_tenant")) == "Test Tenant"
