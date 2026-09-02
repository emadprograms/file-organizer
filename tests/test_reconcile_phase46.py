import pytest
from pathlib import Path
import json
import yaml
from unittest.mock import patch

from src.reconcile.core import run_reconcile_mode
from src.utils.fs import create_shortcut

class DummyArgs:
    def __init__(self, target_dir, dry_run=False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.command = "reconcile"

def test_phase46_auto_verification(tmp_path):
    house_id = "106"
    target_dir = tmp_path / f"{house_id} - Test House"
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True)
    
    yaml_data = [{"name": "Tenant", "start_date": "2021-01-01", "end_date": "present"}]
    with open(source_dir / f"{house_id}_tenants.yaml", "w") as f:
        yaml.dump(yaml_data, f)
        
    state_data = {
        "house_id": house_id,
        "cleaned_pages": [{
            "category": "others",
            "content_explanation": "test",
            "original_index": 0,
            "user_locked": False,
            "canonical_tenant": "Tenant"
        }],
        "grouped_documents": [{
            "start_page": 0,
            "end_page": 0,
            "primary_tenant": "Tenant",
            "category": "others",
            "dates": []
        }],
        "routed_documents": {"per_page": [{
            "page_index": 0,
            "vault_id": "test_page_1",
            "target_folder": "Tenant",
            "output_file": f"{house_id} - Test House/Tenant/test_page_1.lnk",
            "tenant": "Tenant"
        }]}
    }
    with open(source_dir / f"{house_id}_state.json", "w") as f:
        json.dump(state_data, f)
        
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    vault_pdf = vault_dir / "doc_test_page_1.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(vault_pdf, "wb") as f:
        writer.write(f)
    
    # We create the shortcut to make it valid
    tenant_dir = target_dir / "Tenant"
    tenant_dir.mkdir(parents=True)
    create_shortcut(str(vault_pdf.resolve()), str((tenant_dir / "test_page_1.lnk").resolve()))
    
    args = DummyArgs(target_dir=target_dir)
    with patch("src.reconcile.core.FileOrganizer") as mock_org:
        mock_instance = mock_org.return_value
        mock_instance.compute_tenant_folders.return_value = ({"Tenant": "Tenant"}, "Tenant")
        
        # Test verification and report generation
        with patch("src.core.verification.run_verification") as mock_verify:
            mock_verify.return_value = 0 # success
            result = run_reconcile_mode(args)
            
            assert not mock_verify.called
            assert result == 0
    
    new_house_dir = tmp_path / f"{house_id} - Tenant"
    state_file = new_house_dir / ".source_files" / f"{house_id}_state.json"
    assert state_file.exists()
