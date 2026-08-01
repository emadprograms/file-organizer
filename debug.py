import sys
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

tmp_path = Path("C:/Users/Emad/Documents/GitHub/file-organizer/debug_test")
if tmp_path.exists():
    shutil.rmtree(tmp_path, ignore_errors=True)
tmp_path.mkdir(parents=True)

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

canonical_folder = "Test Tenant (2021 - 2025)"
ghost_lnk_path = target_dir / canonical_folder / "01_Ghost" / "2021-01-02 - Ghost Doc.lnk"
ghost_lnk_path.parent.mkdir(parents=True)
create_shortcut(str(ghost_vault_pdf.resolve()), str(ghost_lnk_path.resolve()))

args = DummyArgs(target_dir=target_dir)

# Run 1: Normal processing
import logging
logging.basicConfig(level=logging.INFO)
run_reconcile_mode(args)

# Read the generated tenants to see if they got lost
import yaml
with open(source_dir / f"{house_id}_tenants.yaml", "r", encoding='utf-8') as f:
    print("YAML Data:", yaml.safe_load(f))
    
with open(source_dir / f"reconcile_report.json", "r", encoding='utf-8') as f:
    print("Report:", json.load(f))

new_target_dir = target_dir
for candidate in target_dir.parent.iterdir():
    if candidate.is_dir() and (candidate / ".source_files").exists():
        new_target_dir = candidate
        break

print("AFTER RUN 1: File tree of", new_target_dir)
for root, dirs, files in os.walk(new_target_dir):
    for f in files:
        print(Path(root) / f)

print("\nRunning Verification explicitly on", new_target_dir)
from src.core.verification import run_verification
run_verification(new_target_dir)

print("\nAFTER RUN 2:")
args.target_dir = new_target_dir
run_reconcile_mode(args)
for root, dirs, files in os.walk(new_target_dir):
    for f in files:
        print(Path(root) / f)
