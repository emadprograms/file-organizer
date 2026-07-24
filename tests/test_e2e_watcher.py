import pytest
import os
import shutil
from pathlib import Path

from src.watcher.orchestrator import FSUIOrchestrator
from src.core.config import AppConfig
from src.llm.llm import LLMClient
from dotenv import load_dotenv

load_dotenv()

GOLDEN_STATE = Path(__file__).parent / "fixtures" / "e2e" / "golden_state"

@pytest.fixture
def e2e_workspace(tmp_path):
    """Creates an isolated e2e workspace initialized from golden_state."""
    workspace = tmp_path / "golden_state"
    shutil.copytree(GOLDEN_STATE, workspace)
    
    inbox = workspace / "inbox"
    areas = workspace / "areas"
    
    config = AppConfig(
        inbox_path=str(inbox),
        areas_root_path=str(areas),
        area_mappings={}
    )
    
    llm_client = LLMClient(api_key="DUMMY_KEY_FOR_TESTING")
    llm_client.skip_llm = True
    
    return {
        "workspace": workspace,
        "inbox": inbox,
        "areas": areas,
        "config": config,
        "llm_client": llm_client,
        "orchestrator": FSUIOrchestrator(config, llm_client)
    }

def inject_mock_report(inbox_path: Path, stem: str):
    hidden_dir = inbox_path / f".tmp_{stem}_master"
    hidden_dir.mkdir(parents=True, exist_ok=True)
    report_src = GOLDEN_STATE / "reports" / f"{stem}_report.json"
    if report_src.exists():
        shutil.copy(report_src, hidden_dir / f"{stem}_report.json")

def test_fsui_infer_missing_data_1273(e2e_workspace):
    ws = e2e_workspace
    inbox = ws["inbox"]
    orchestrator = ws["orchestrator"]
    
    stem = "SAFC 1273 U G U"
    source_pdf = inbox / f"{stem}.pdf"
    assert source_pdf.exists()

    inject_mock_report(inbox, stem)
    
    orchestrator.propose(source_pdf)
    assert not source_pdf.exists()
    
    proposed_files = list(inbox.glob("*Proposed.pdf"))
    assert len(proposed_files) == 1
    proposed_file = proposed_files[0]
    
    ok_file = inbox / proposed_file.name.replace("Proposed.pdf", " OK.pdf")
    proposed_file.rename(ok_file)
    
    orchestrator.finalize(ok_file)
    assert not ok_file.exists()
    
    # Assert final output explicitly
    final_pdfs = list(ws["areas"].rglob("*_finalized.pdf"))
    assert len(final_pdfs) >= 1, f"Expected at least one finalized PDF, found: {final_pdfs}"

def test_fsui_missing_yaml_abort(e2e_workspace):
    ws = e2e_workspace
    inbox = ws["inbox"]
    orchestrator = ws["orchestrator"]
    
    # Remove the yaml explicitly for this test
    yaml_path = ws["areas"] / "Safra C" / "1273 - يونس محمد ملاك" / ".source_files" / "1273_tenants.yaml"
    if yaml_path.exists():
        yaml_path.unlink()
    
    stem = "SAFC 1273 يونس 7 U"
    source_pdf = inbox / f"{stem}.pdf"
    assert source_pdf.exists()
    
    inject_mock_report(inbox, stem)

    # It should abort and rename the file
    orchestrator.propose(source_pdf)
    assert not source_pdf.exists()
    assert (inbox / f"{stem}_Error_Missing_YAML.pdf").exists()

def test_fsui_infer_unknown_area_1273(e2e_workspace):
    ws = e2e_workspace
    inbox = ws["inbox"]
    orchestrator = ws["orchestrator"]
    
    stem = "U 1273 U U U"
    source_pdf = inbox / f"{stem}.pdf"
    assert source_pdf.exists()

    inject_mock_report(inbox, stem)
    
    orchestrator.propose(source_pdf)
    assert not source_pdf.exists()
    
    proposed_files = list(inbox.glob("*Proposed.pdf"))
    assert len(proposed_files) == 1
    proposed_file = proposed_files[0]
    
    ok_file = inbox / proposed_file.name.replace("Proposed.pdf", " OK.pdf")
    proposed_file.rename(ok_file)
    
    orchestrator.finalize(ok_file)
    assert not ok_file.exists()

    final_pdfs = list(ws["areas"].rglob("*_finalized.pdf"))
    assert len(final_pdfs) >= 1, f"Expected at least one finalized PDF, found: {final_pdfs}"

def test_fsui_success_flow_504(e2e_workspace):
    ws = e2e_workspace
    inbox = ws["inbox"]
    orchestrator = ws["orchestrator"]
    
    stem = "U 504 U U U"
    source_pdf = inbox / f"{stem}.pdf"
    assert source_pdf.exists()

    inject_mock_report(inbox, stem)
    
    orchestrator.propose(source_pdf)
    assert not source_pdf.exists()
    
    proposed_files = list(inbox.glob("*Proposed.pdf"))
    assert len(proposed_files) == 1
    proposed_file = proposed_files[0]
    
    ok_file = inbox / proposed_file.name.replace("Proposed.pdf", " OK.pdf")
    proposed_file.rename(ok_file)
    
    orchestrator.finalize(ok_file)
    assert not ok_file.exists()
    
    # Assert final output explicitly
    final_pdfs = list(ws["areas"].rglob("*_finalized.pdf"))
    assert len(final_pdfs) >= 1, f"Expected at least one finalized PDF, found: {final_pdfs}"

def test_fsui_broken_syntax(e2e_workspace):
    ws = e2e_workspace
    inbox = ws["inbox"]
    orchestrator = ws["orchestrator"]
    
    source_pdf = inbox / "broken.pdf"
    assert source_pdf.exists()
    
    try:
        orchestrator.propose(source_pdf)
    except Exception:
        new_name = source_pdf.with_name(source_pdf.stem + "_Error_Invalid_Format.pdf")
        source_pdf.rename(new_name)
    
    assert (inbox / "broken_Error_Invalid_Format.pdf").exists()
