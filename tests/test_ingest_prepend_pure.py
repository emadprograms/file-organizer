import pytest
from pathlib import Path
import json
import uuid
from src.main import get_parser
from src.ingest.core import run_ingest_mode
from src.reconcile.core import run_reconcile_mode
from src.core.config import AppConfig
from src.core.schemas import DocumentGroup
from src.core.models import PageData
from unittest.mock import patch, MagicMock

class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@patch("src.pipeline.pipeline.Pipeline._clean_documents")
@patch("src.categorization.fine_categorization.process_fine_categorization")
@patch("src.pipeline.pipeline.Pipeline._group_documents")
@patch("src.pipeline.pipeline.Pipeline._route_documents")
def test_pure_ingest_prepend(mock_route, mock_group, mock_fine, mock_clean, tmp_path):
    house_id = "514"
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    target_dir = areas_root / f"{house_id} - John Doe"
    target_dir.mkdir(parents=True, exist_ok=True)
    source_dir = target_dir / ".source_files"
    source_dir.mkdir(parents=True, exist_ok=True)
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = tmp_path / "config.yaml"
    import yaml
    with open(config_path, "w") as f:
        yaml.dump({"areas_root_path": str(areas_root), "inbox_path": str(tmp_path / "inbox")}, f)
    config = AppConfig.load(config_path)
    
    # 1. Create an existing state.json with 1 document (1 page)
    old_vault_id = uuid.uuid4().hex
    initial_state = {
        "cleaned_pages": [
            {"original_index": 0, "category": "letters", "expected_tenant_name": "John Doe", "date": "2023-01-01", "canonical_tenant": "John Doe"}
        ],
        "fine_categorized_pages": [
            {"original_index": 0, "category": "letters", "expected_tenant_name": "John Doe", "date": "2023-01-01", "canonical_tenant": "John Doe"}
        ],
        "grouped_documents": [
            {"start_page": 0, "end_page": 0, "primary_tenant": "John Doe", "category": "letters", "vault_id": old_vault_id, "dates": ["2023-01-01"]}
        ],
        "manifest": {
            "summary": {"total_output_pages": 1, "output_file_count": 1},
            "per_page": [
                {
                    "page_index": 0, "vault_id": old_vault_id,
                    "output_file": f"{house_id} - John Doe/John Doe/Letters/001.pdf",
                    "target_folder": "John Doe/Letters", "canonical_tenant": "John Doe", "category": "letters"
                }
            ]
        }
    }
    state_file = source_dir / f"{house_id}_state.json"
    with open(state_file, "w") as f:
        json.dump(initial_state, f)
        
    # Create the old vault file
    old_vault_pdf = vault_dir / f"doc_{old_vault_id}.pdf"
    old_vault_pdf.touch()
    
    # 2. Drop a NEW PDF in the root
    raw_pdf_path = target_dir / "514.pdf"
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100) # 2 pages
    with open(raw_pdf_path, "wb") as f:
        writer.write(f)
        
    # Create raw_dump for 514
    dump_data = [
        {"expected_house_number": house_id, "expected_tenant_name": "John Doe", "category": "others", "date": "2024-01-01"},
        {"expected_house_number": house_id, "expected_tenant_name": "John Doe", "category": "others", "date": "2024-01-01"}
    ]
    with open(target_dir / "514.raw_dump.json", "w") as f:
        json.dump(dump_data, f)
        
    # Mocks for the new PDF
    mock_clean.return_value = (
        [
            PageData(category="others", date="2024-01-01", original_index=0, expected_tenant_name="John Doe", canonical_tenant="John Doe"),
            PageData(category="others", date="2024-01-01", original_index=1, expected_tenant_name="John Doe", canonical_tenant="John Doe")
        ],
        [{"name": "John Doe", "start_date": "2021-01-01", "end_date": "present"}]
    )
    mock_fine.return_value = mock_clean.return_value[0]
    mock_group.return_value = [DocumentGroup(
        start_page=0, end_page=1, primary_tenant="John Doe",
        category="others", dates=["2024-01-01"], reason="mock"
    )]
    mock_route.return_value = [DocumentGroup(
        start_page=0, end_page=1, primary_tenant="John Doe",
        category="others", dates=["2024-01-01"], reason="mock", vault_id="new_vault"
    )]

    # 3. Run ingest
    args = DummyArgs(command="ingest", input_path=target_dir, dry_run=False, verbose=False)
    mock_llm = MagicMock()
    result = run_ingest_mode(args, config, mock_llm)
    assert result == 0
    
    # 4. Assert ingest ONLY updated state.json and did not extract vault PDF
    assert raw_pdf_path.exists(), "514.pdf should still be in root!"
    print("VAULT DIR CONTENTS:", list(vault_dir.iterdir()))
    assert not (vault_dir / "doc_new_vault.pdf").exists(), "Vault PDF should NOT be extracted by ingest!"
    
    with open(source_dir / f"{house_id}_state.json", "r") as f:
        state_data = json.load(f)
        
    # The old document (which was at index 0) should now be shifted by 2
    assert state_data["cleaned_pages"][2]["original_index"] == 2
    assert state_data["grouped_documents"][1]["start_page"] == 2
    
    # The new document should have source_pdf injected
    new_doc = state_data["grouped_documents"][0]
    assert new_doc.get("source_pdf") == "514.pdf"
    assert new_doc.get("relative_start_page") == 0
    assert new_doc.get("relative_end_page") == 1
    
    print("ROUTED_DOCUMENTS_PER_PAGE:", state_data["manifest"]["per_page"])
    old_route = state_data["manifest"]["per_page"][2]
    assert old_route["page_index"] == 2
    
    assert state_data["manifest"]["summary"]["total_output_pages"] == 3
    
    # 5. Run reconcile
    rec_args = DummyArgs(command="reconcile", target_dir=target_dir, dry_run=False, verbose=False, tenants=False)
    result = run_reconcile_mode(rec_args)
    assert result == 0
    
    # 6. Assert reconcile extracted the PDF
    assert not raw_pdf_path.exists(), "reconcile should have deleted 514.pdf"
    assert (vault_dir / "doc_new_vault.pdf").exists(), "reconcile should have extracted the vault PDF!"
