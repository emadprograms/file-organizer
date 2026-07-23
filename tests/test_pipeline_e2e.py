import os
import sys
import json
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.core.config import AppConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "e2e" / "golden_state"

def inject_mock_report(inbox: Path, stem: str) -> None:
    """Inject the mock report for the given stem into the master inbox directory."""
    master_dir = inbox / f".tmp_{stem}_master"
    master_dir.mkdir(exist_ok=True)
    
    parts = stem.split(" ")
    tenant_hint = parts[2] if len(parts) > 2 else "U"
    group = parts[3] if len(parts) > 3 else "G"
    
    if group == "G":
        folder_name = "01_عقود"
    elif group == "7":
        folder_name = "07_رخص"
    else:
        folder_name = "01_عقود"
        
    if "504" in stem:
        category = "letters"
        date = "2021-05-24"
        expected_tenant_name = "أحمد يوسف المريسل"
        expected_house_number = "504"
    else:
        category = "contract"
        date = "2006-04-18" if "1273" in stem else "2015-05-05"
        expected_tenant_name = tenant_hint
        expected_house_number = stem.split(" ")[1] if len(stem.split(" ")) > 1 else "U"

    mock_data = {
        "0": {
            "category": category,
            "content_explanation": "dummy",
            "date": date,
            "expected_tenant_name": expected_tenant_name,
            "expected_house_number": expected_house_number
        }
    }
    
    with open(master_dir / f"{stem}_report.json", "w", encoding="utf-8") as f:
        json.dump(mock_data, f, ensure_ascii=False)

def create_workspace(tmp_path: Path, house: str = "1273") -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    inbox = workspace / "inbox"
    inbox.mkdir()
    areas = workspace / "areas"
    areas.mkdir()

    if house == "1273":
        safc_dir = areas / "Safra C"
        safc_dir.mkdir()
        shutil.copytree(FIXTURES_DIR / "areas" / "Safra C" / "1273 - يونس محمد ملاك", safc_dir / "1273 - يونس محمد ملاك")
    elif house == "504":
        safd_dir = areas / "Safra D"
        safd_dir.mkdir()
        shutil.copytree(FIXTURES_DIR / "areas" / "Safra D" / "504 - أحمد يوسف المريسل", safd_dir / "504 - أحمد يوسف المريسل")

    config_path = workspace / "config.yaml"
    config_path.write_text(f"inbox_path: {inbox}\nareas_root_path: {areas}\narea_mappings: {{}}", encoding="utf-8")
    os.environ["FILE_ORGANIZER_CONFIG"] = str(config_path)

    return workspace, inbox, areas

@patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
def test_cli_append_1273(tmp_path) -> None:
    workspace, inbox, areas = create_workspace(tmp_path, "1273")
    stem = "SAFC 1273 U G U"
    
    shutil.copy(FIXTURES_DIR / "inbox" / f"{stem}.pdf", inbox / f"{stem}.pdf")
    inject_mock_report(inbox, stem)
    
    test_args = ["main.py", "append", "--skip-llm"]
    
    with patch("src.main.LLMClient") as MockLLMClient, patch("src.fs_ui.orchestrator.time.sleep", side_effect=[None, SystemExit(0)]):
        mock_client = MockLLMClient.return_value
        mock_client.skip_llm = True
        
        with patch.object(sys, 'argv', test_args):
            from src.main import main
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0
            
    proposed_files = list(inbox.glob("*_Proposed.pdf"))
    print('\nINBOX AFTER TEST:', list(inbox.glob('*')))
    assert len(proposed_files) == 1
    assert proposed_files[0].name == "Safra C 1273 يونس محمد مالك 5 2006-04-18 عقد_Proposed.pdf"

@patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
def test_cli_append_1273_tenant_folder(tmp_path) -> None:
    workspace, inbox, areas = create_workspace(tmp_path, "1273")
    stem = "SAFC 1273 يونس 7 U"
    
    shutil.copy(FIXTURES_DIR / "inbox" / f"{stem}.pdf", inbox / f"{stem}.pdf")
    inject_mock_report(inbox, stem)
    
    test_args = ["main.py", "append", "--skip-llm"]
    
    with patch("src.main.LLMClient") as MockLLMClient, patch("src.fs_ui.orchestrator.time.sleep", side_effect=[None, SystemExit(0)]):
        mock_client = MockLLMClient.return_value
        mock_client.skip_llm = True
        
        with patch.object(sys, 'argv', test_args):
            from src.main import main
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0
            
    proposed_files = list(inbox.glob("*_Proposed.pdf"))
    print('\nINBOX AFTER TEST:', list(inbox.glob('*')))
    assert len(proposed_files) == 1
    assert proposed_files[0].name == "Safra C 1273 يونس G 2006-04-18 Unknown_Proposed.pdf"

@patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
def test_cli_append_1273_unknown(tmp_path) -> None:
    workspace, inbox, areas = create_workspace(tmp_path, "1273")
    stem = "U 1273 U U U"
    
    shutil.copy(FIXTURES_DIR / "inbox" / f"{stem}.pdf", inbox / f"{stem}.pdf")
    inject_mock_report(inbox, stem)
    
    test_args = ["main.py", "append", "--skip-llm"]
    
    with patch("src.main.LLMClient") as MockLLMClient, patch("src.fs_ui.orchestrator.time.sleep", side_effect=[None, SystemExit(0)]):
        mock_client = MockLLMClient.return_value
        mock_client.skip_llm = True
        
        with patch.object(sys, 'argv', test_args):
            from src.main import main
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0
            
    proposed_files = list(inbox.glob("*_Proposed.pdf"))
    print('\nINBOX AFTER TEST:', list(inbox.glob('*')))
    assert len(proposed_files) == 1
    assert proposed_files[0].name == "Safra C 1273 يونس محمد مالك 5 2006-04-18 عقد_Proposed.pdf"

@patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
def test_cli_append_504(tmp_path) -> None:
    workspace, inbox, areas = create_workspace(tmp_path, "504")
    stem = "U 504 U U U"
    
    shutil.copy(FIXTURES_DIR / "inbox" / f"{stem}.pdf", inbox / f"{stem}.pdf")
    inject_mock_report(inbox, stem)
    
    test_args = ["main.py", "append", "--skip-llm"]
    
    with patch("src.main.LLMClient") as MockLLMClient, patch("src.fs_ui.orchestrator.time.sleep", side_effect=[None, SystemExit(0)]):
        mock_client = MockLLMClient.return_value
        mock_client.skip_llm = True
        
        with patch.object(sys, 'argv', test_args):
            from src.main import main
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0
            
    proposed_files = list(inbox.glob("*_Proposed.pdf"))
    print('\nINBOX AFTER TEST:', list(inbox.glob('*')))
    assert len(proposed_files) == 1
    assert proposed_files[0].name == "Safra D 504 أحمد يوسف المريسل 13 2021-05-24 عنوان تجريبي_Proposed.pdf"

@patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
def test_cli_append_broken(tmp_path) -> None:
    workspace, inbox, areas = create_workspace(tmp_path, "1273")
    stem = "broken"
    
    shutil.copy(FIXTURES_DIR / "inbox" / f"{stem}.pdf", inbox / f"{stem}.pdf")
    inject_mock_report(inbox, stem)
    
    test_args = ["main.py", "append", "--skip-llm"]
    
    with patch("src.main.LLMClient") as MockLLMClient, patch("src.fs_ui.orchestrator.time.sleep", side_effect=[None, SystemExit(0)]):
        mock_client = MockLLMClient.return_value
        mock_client.skip_llm = True
        
        with patch.object(sys, 'argv', test_args):
            from src.main import main
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0
            
    # Broken filename doesn't follow pattern, should be marked as failed
    failed_files = list(inbox.glob("*_Error_Invalid_Format.pdf"))
    print("\nINBOX AFTER TEST:", list(inbox.glob("*")))
    assert len(failed_files) == 1
