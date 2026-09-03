import os
import json
import pytest
import subprocess
import time
from pathlib import Path
from playwright.sync_api import Page, expect

@pytest.fixture(scope="module")
def mock_areas_server(tmp_path_factory):
    areas_root = tmp_path_factory.mktemp("areas")
    
    # Safra D setup
    house_d = areas_root / "Safra D" / "502 - Test" / ".source_files"
    house_d.mkdir(parents=True)
    state_json_d = {
        "grouped_documents": [
            {"primary_tenant": "NewTenant", "category": "letters", "dates": ["2025-01-01"], "brief_arabic_title": "Test Title Grouped", "vault_id": None, "is_direct_routed": True}
        ],
        "routed_documents": [
            {"primary_tenant": "NewTenant", "category": "letters", "dates": ["2025-01-01"], "brief_arabic_title": "Test Title Routed", "vault_id": "real-vault-id", "is_direct_routed": True}
        ],
        "manifest": {"per_page": [{"tenant": "NewTenant", "target_folder": "present"}]}
    }
    with open(house_d / "502_state.json", "w", encoding="utf-8") as f:
        json.dump(state_json_d, f)
        
    # Safra C setup
    house_c = areas_root / "Safra C" / "123 - Old Format" / ".source_files"
    house_c.mkdir(parents=True)
    state_json_c = {
        "grouped_documents": [
            {"primary_tenant": "OldTenant", "category": "letters", "dates": ["2023-01-01"], "brief_arabic_title": "Test Title Old Format", "vault_id": "old-vault-id", "is_direct_routed": False}
        ],
        "manifest": {"per_page": [{"tenant": "OldTenant", "target_folder": "present"}]},
        "manifest": {}
    }
    with open(house_c / "123_state.json", "w", encoding="utf-8") as f:
        json.dump(state_json_c, f)
        
    config_path = areas_root / "config.yaml"
    with open(config_path, "w") as f:
        f.write(f'inbox_path: "{areas_root}/inbox"\n')
        f.write(f'areas_root_path: "{areas_root}"\n')
        f.write('area_mappings: {}\n')
        
    env = os.environ.copy()
    env["FILE_ORGANIZER_CONFIG"] = str(config_path)
    
    process = subprocess.Popen(
        [".venv/bin/python", "-m", "uvicorn", "src.api.server:app", "--host", "127.0.0.1", "--port", "8005", "--log-level", "error"],
        env=env
    )
    time.sleep(2)
    yield "http://127.0.0.1:8005"
    process.terminate()
    process.wait()

def test_safra_d_backend_fix_with_playwright(page: Page, mock_areas_server):
    page.goto(mock_areas_server)
    page.click("text=Safra D")
    page.click("text=502 - Test")
    page.click("text=NewTenant")
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("Test Title Routed", timeout=5000)

def test_safra_c_backward_compatibility(page: Page, mock_areas_server):
    page.goto(mock_areas_server)
    page.click("text=Safra C")
    page.click("text=123 - Old Format")
    page.click("text=OldTenant")
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("Test Title Old Format", timeout=5000)
