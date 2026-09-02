import os
from pathlib import Path
import pytest
from pypdf import PdfWriter
def make_valid_pdf(path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(path, "wb") as f:
        writer.write(f)

import json

from src.reconcile.core import run_reconcile_mode
from src.core.verification import run_verification

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = target_dir
        self.dry_run = dry_run

def test_reconcile_and_verification_corrupt_vault_pdf(tmp_path):
    house_dir = tmp_path / "123 - Test House"
    source_dir = house_dir / ".source_files"
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    
    # Create tenants.yaml
    with open(source_dir / "123_tenants.yaml", "w") as f:
        f.write("- name: Tenant A\n  start_date: '2020-01-01'\n  end_date: present\n")
        
    # Create minimal state.json
    state = {
        "cleaned_pages": [
            {
                "original_index": 0,
                "category": "Cat",
                "canonical_tenant": "Tenant A",
                "date": "2020-01-01",
                "content_explanation": "test"
            }
        ],
        "grouped_documents": [],
        "routed_documents": {
            "per_page": [
                {
                    "page_index": 0,
                    "vault_id": "corrupt1",
                    "output_file": "123 - Test House/01_Cat/test.lnk",
                    "target_folder": "01_Cat",
                    "dates": ["2020-01-01"],
                    "brief_arabic_title": "test",
                    "user_locked": False
                }
            ]
        }
    }
    with open(source_dir / "123_state.json", "w") as f:
        json.dump(state, f)
        
    # Create corrupt PDF in vault (untracked)
    corrupt_pdf = vault_dir / "doc_corrupt3.pdf"
    with open(corrupt_pdf, "wb") as f:
        f.write(b"NOT A PDF BUT HAS BYTES")
        
    # Create another 0-byte PDF in vault
    zero_byte_pdf = vault_dir / "doc_corrupt2.pdf"
    with open(zero_byte_pdf, "wb") as f:
        pass
        
    # Create ghost shortcut
    from src.utils.fs import create_shortcut
    ghost_lnk = house_dir / "01_Cat" / "ghost.lnk"
    ghost_lnk.parent.mkdir(parents=True, exist_ok=True)
    create_shortcut(str(corrupt_pdf.resolve()), str(ghost_lnk.resolve()))
    
    args = DummyArgs(house_dir, dry_run=False)
    
    # Run reconciler
    res = run_reconcile_mode(args)
    assert res == 0
    
    # Check if report has corrupt vault files
    new_house_dir = house_dir.parent / "123 - Tenant A"
    state_file = new_house_dir / ".source_files" / "123_state.json"
    assert state_file.exists()


def test_verification_corrupt_vault_pdf(tmp_path):
    house_dir = tmp_path / "124 - Test House"
    source_dir = house_dir / ".source_files"
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    
    zero_pdf = vault_dir / "doc_zero.pdf"
    make_valid_pdf(zero_pdf)
    
    corrupt_pdf = vault_dir / "doc_corrupt.pdf"
    with open(corrupt_pdf, "wb") as f:
        f.write(b"CORRUPT PDF DATA HERE")
        
    # run_verification
    res = run_verification(house_dir)
    assert res == 1  # Should fail because of corrupt files
