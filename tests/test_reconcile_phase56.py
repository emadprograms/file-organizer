import pytest
from pathlib import Path
import json
import yaml
import os
import shutil
import time

from src.reconcile.core import run_reconcile_mode
from src.utils.fs import create_shortcut

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"

def test_idempotency_phase56(tmp_path):
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
        "routed_documents": {
            "per_page": []
        }
    }
    with open(source_dir / f"{house_id}_state.json", "w", encoding='utf-8') as f:
        json.dump(state_data, f)
        
    # Create a raw PDF to trigger ingestion
    raw_pdf_path = target_dir / "2021-01-01 - Raw Document.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(raw_pdf_path, "wb") as f:
        writer.write(f)
        
    # Also create a ghost shortcut scenario by faking a vault document that isn't in state.json
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True)
    ghost_vault_pdf = vault_dir / "doc_GHOST123.pdf"
    with open(ghost_vault_pdf, "wb") as f:
        writer.write(f)
        
    canonical_folder = "Test Tenant \u200E(2021 - 2025)\u200E"
    ghost_lnk_path = target_dir / canonical_folder / "01_Ghost" / "2021-01-02 - Ghost Doc.lnk"
    ghost_lnk_path.parent.mkdir(parents=True)
    create_shortcut(str(ghost_vault_pdf.resolve()), str(ghost_lnk_path.resolve()))
    
    args = DummyArgs(target_dir=target_dir)
    
    # Run 1: Normal processing
    result1 = run_reconcile_mode(args)
    assert result1 == 0
    
    # Update target_dir to the new resolved one
    new_target_dir = target_dir
    for candidate in target_dir.parent.iterdir():
        if candidate.is_dir() and (candidate / ".source_files").exists():
            new_target_dir = candidate
            break
            
    source_dir = new_target_dir / ".source_files"
    
    # Verify standard actions occurred
    report_path = source_dir / "reconcile_report.json"
    with open(report_path, "r", encoding='utf-8') as f:
        report1 = json.load(f)
    assert report1["raw_pdf_ingested"] == 1
    assert report1["ghost_adopted"] == 1
    
    # Wait slightly to ensure mtimes would be different if written
    time.sleep(2)
    
    # Capture exactly the state and mtimes
    state_file = source_dir / f"{house_id}_state.json"
    state_content_run1 = state_file.read_text(encoding='utf-8')
    
    # Find all files and their mtimes
    def get_mtimes():
        mtimes = {}
        for root, dirs, files in os.walk(target_dir.parent):
            for file in files:
                filepath = Path(root) / file
                mtimes[str(filepath)] = filepath.stat().st_mtime
        return mtimes
        
    mtimes_run1 = get_mtimes()
    
    args.target_dir = new_target_dir
    
    # Run 2: Idempotent run
    result2 = run_reconcile_mode(args)
    assert result2 == 0
    
    with open(new_target_dir / ".source_files" / "reconcile_report.json", "r", encoding='utf-8') as f:
        report2 = json.load(f)
        
    assert report2["raw_pdf_ingested"] == 0
    assert report2["ghost_adopted"] == 0
    assert report2["shortcuts_repaired"] == 0
    assert report2["file_moves_planned"] == 0
    
    state_content_run2 = (new_target_dir / ".source_files" / f"{house_id}_state.json").read_text(encoding='utf-8')
    if state_content_run1 != state_content_run2:
        import difflib
        diff = list(difflib.unified_diff(
            state_content_run1.splitlines(),
            state_content_run2.splitlines(),
            fromfile='run1.json',
            tofile='run2.json'
        ))
        print("\n".join(diff))
    assert state_content_run1 == state_content_run2, "state.json should be identical byte-for-byte"
    
    mtimes_run2 = get_mtimes()
    
    # Exclude reconcile_report.json because it always gets written at the end of run_reconcile_mode
    # Exclude state.json because we already tested it above and its mtime may change if we don't prevent writing completely? No, we prevented writing
    for filepath, mtime in mtimes_run1.items():
        if "reconcile_report.json" in filepath or "_report.json" in filepath:
            continue
        # Also verification output might get written, exclude it
        if "verification_report" in filepath or "verification" in filepath:
            continue
        # The timeline folder might be rebuilt entirely if not idempotent
        assert mtimes_run2[filepath] == mtime, f"File {filepath} was modified!"
        
    # Run 3: Just to be absolutely sure
    time.sleep(2)
    result3 = run_reconcile_mode(args)
    assert result3 == 0
    
    with open(new_target_dir / ".source_files" / "reconcile_report.json", "r", encoding='utf-8') as f:
        report3 = json.load(f)
        
    assert report3["raw_pdf_ingested"] == 0
    assert report3["ghost_adopted"] == 0
    
    mtimes_run3 = get_mtimes()
    for filepath, mtime in mtimes_run2.items():
        if "reconcile_report.json" in filepath or "_report.json" in filepath or "verification" in filepath:
            continue
        assert mtimes_run3[filepath] == mtime, f"File {filepath} was modified on run 3!"
