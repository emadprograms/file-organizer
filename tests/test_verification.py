import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.core.verification import run_verification
from src.utils.fs import create_shortcut

def make_valid_pdf(path: Path):
    import pypdf
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(path, "wb") as f:
        writer.write(f)

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
    make_valid_pdf(pdf1)
    pdf2 = vault_dir / "doc_2.pdf"
    make_valid_pdf(pdf2)
    
    # Shortcuts
    lnk1 = tenant_a / "doc1.lnk"
    lnk2 = timeline / "doc2.lnk"
    
    create_shortcut(str(pdf1), str(lnk1))
    create_shortcut(str(pdf2), str(lnk2))
    
    # State JSON
    state_file = source_dir / "123_state.json"
    state_data = {
        "cleaned_pages": [{}],
        "grouped_documents": [
            {
                "vault_id": "1",
                "shortcuts": ["Tenant A \u200e(2023 - 2024)\u200e/doc1.lnk"]
            }
        ],
        "manifest": {
            "per_page": [
                {"output_file": "123 - Test House/Tenant A \u200e(2023 - 2024)\u200e/doc1.lnk"}
            ],
            "summary": {
                "total_input_pages": 1
            }
        }
    }
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f)
        
    # Report JSON
    report_file = source_dir / "123_report.json"
    report_data = [
        {
            "vault_id": "1",
            "start_page": 1,
            "end_page": 1,
            "date": "2023-01-01",
            "folder_path": "Tenant A",
            "filename": "doc_1.pdf",
            "tenant": "Tenant A"
        }
    ]
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f)
        
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
    make_valid_pdf(mock_house / ".source_files" / "123_1_cleaned.json")
    assert run_verification(mock_house) == 1

def test_verification_invalid_tenant(mock_house):
    (mock_house / "Invalid Tenant").mkdir()
    assert run_verification(mock_house) == 1

def test_verification_rogue_pdf(mock_house):
    make_valid_pdf(mock_house / "Tenant A \u200e(2023 - 2024)\u200e" / "rogue.pdf")
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
    orphan_pdf = mock_house / ".source_files" / "vault" / "orphan.pdf"
    make_valid_pdf(orphan_pdf)
    assert run_verification(mock_house) == 1

def test_verification_missing_state(mock_house):
    (mock_house / ".source_files" / "123_state.json").unlink()
    assert run_verification(mock_house) == 1

def test_verification_missing_state_output(mock_house):
    state_file = mock_house / ".source_files" / "123_state.json"
    state_data = {
        "cleaned_pages": [{}],
        "grouped_documents": [
            {
                "vault_id": "1",
                "shortcuts": ["Tenant A \u200e(2023 - 2024)\u200e/missing.lnk"]
            }
        ],
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
    make_valid_pdf(extra_pdf)
    extra_lnk = mock_house / "Tenant A \u200e(2023 - 2024)\u200e" / "extra.lnk"
    create_shortcut(str(extra_pdf), str(extra_lnk))
    
    # Should still pass, but logs a warning
    assert run_verification(mock_house) == 0
    assert "categorized shortcuts not tracked" in caplog.text

def test_verification_hijacked_shortcut(mock_house):
    # State expects Tenant A/doc1.lnk to point to doc_1.pdf (by virtue of it not being explicitly mocked differently, wait, state says:
    # "manifest": {"per_page": [{"output_file": "...", "vault_id": "1"}]}
    # Let's just update the state explicitly in the test to ensure it expects vault_id "1"
    
    state_file = mock_house / ".source_files" / "123_state.json"
    with open(state_file, "r", encoding="utf-8") as f:
        state_data = json.load(f)
    state_data["manifest"]["per_page"][0]["vault_id"] = "1"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f)
        
    # Hijack doc1.lnk to point to doc_2.pdf
    pdf2 = mock_house / ".source_files" / "vault" / "doc_2.pdf"
    lnk1 = mock_house / "Tenant A \u200e(2023 - 2024)\u200e" / "doc1.lnk"
    create_shortcut(str(pdf2), str(lnk1))
    
    assert run_verification(mock_house) == 1

def test_verification_null_state_arrays(mock_house):
    state_file = mock_house / ".source_files" / "123_state.json"
    with open(state_file, "r", encoding="utf-8") as f:
        state_data = json.load(f)
    state_data["cleaned_pages"] = None
    state_data["grouped_documents"] = None
    state_data["routed_documents"] = None
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f)
        
    assert run_verification(mock_house) == 0
