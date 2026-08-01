import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.core.verification import run_verification
from src.utils.fs import create_shortcut

@pytest.fixture
def mock_house(tmp_path):
    house_dir = tmp_path / "123 - Test House"
    house_dir.mkdir()
    
    source_dir = house_dir / ".source_files"
    source_dir.mkdir()
    
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    
    # tenants.yaml
    with open(source_dir / "tenants.yaml", "w", encoding="utf-8") as f:
        f.write("- name: Tenant A\n- name: Tenant B\n")
        
    # Valid Tenant A
    tenant_a = house_dir / "Tenant A \u200e(2023 - 2024)\u200e"
    tenant_a.mkdir()
    
    # Timeline
    timeline = house_dir / "[Timeline View]"
    timeline.mkdir()
    
    # Vault PDFs
    pdf1 = vault_dir / "doc_1.pdf"
    pdf1.touch()
    pdf2 = vault_dir / "doc_2.pdf"
    pdf2.touch()
    
    # Shortcuts
    lnk1 = tenant_a / "doc1.lnk"
    lnk2 = timeline / "doc2.lnk"
    
    create_shortcut(str(pdf1), str(lnk1))
    create_shortcut(str(pdf2), str(lnk2))
    
    # State JSON
    state_file = source_dir / "123_state.json"
    state_data = {
        "manifest": {
            "per_page": [
                {"output_file": "123 - Test House/Tenant A \u200e(2023 - 2024)\u200e/doc1.lnk"}
            ]
        }
    }
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f)
        
    return house_dir

def test_verification_missing_dir(tmp_path):
    assert run_verification(tmp_path / "missing") == 1

def test_verification_empty_dir(tmp_path):
    assert run_verification(tmp_path) == 1

def test_verification_healthy_house(mock_house):
    assert run_verification(mock_house) == 0

def test_verification_missing_vault(mock_house):
    vault = mock_house / ".source_files" / "vault"
    for f in vault.iterdir():
        f.unlink()
    vault.rmdir()
    assert run_verification(mock_house) == 1

def test_verification_legacy_json(mock_house):
    (mock_house / ".source_files" / "123_1_cleaned.json").touch()
    assert run_verification(mock_house) == 1

def test_verification_invalid_tenant(mock_house):
    (mock_house / "Invalid Tenant").mkdir()
    assert run_verification(mock_house) == 1

def test_verification_rogue_pdf(mock_house):
    (mock_house / "Tenant A \u200e(2023 - 2024)\u200e" / "rogue.pdf").touch()
    assert run_verification(mock_house) == 1

def test_verification_broken_shortcut(mock_house):
    # Delete a vault file so its shortcut breaks
    (mock_house / ".source_files" / "vault" / "doc_1.pdf").unlink()
    assert run_verification(mock_house) == 1

def test_verification_shortcut_outside_vault(mock_house):
    outside_file = mock_house / ".source_files" / "tenants.yaml"
    bad_lnk = mock_house / "Tenant A \u200e(2023 - 2024)\u200e" / "bad.lnk"
    create_shortcut(str(outside_file), str(bad_lnk))
    assert run_verification(mock_house) == 1

def test_verification_orphan_pdf(mock_house):
    (mock_house / ".source_files" / "vault" / "orphan.pdf").touch()
    assert run_verification(mock_house) == 1

def test_verification_missing_state(mock_house):
    (mock_house / ".source_files" / "123_state.json").unlink()
    assert run_verification(mock_house) == 1

def test_verification_missing_state_output(mock_house):
    state_file = mock_house / ".source_files" / "123_state.json"
    state_data = {
        "manifest": {
            "per_page": [
                {"output_file": "123 - Test House/Tenant A \u200e(2023 - 2024)\u200e/missing.lnk"}
            ]
        }
    }
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f)
    assert run_verification(mock_house) == 1

def test_verification_untracked_shortcut_warning(mock_house, caplog):
    # Add a valid shortcut not in state.json
    extra_pdf = mock_house / ".source_files" / "vault" / "doc_3.pdf"
    extra_pdf.touch()
    extra_lnk = mock_house / "Tenant A \u200e(2023 - 2024)\u200e" / "extra.lnk"
    create_shortcut(str(extra_pdf), str(extra_lnk))
    
    # Should still pass, but logs a warning
    assert run_verification(mock_house) == 0
    assert "categorized shortcuts not tracked" in caplog.text
