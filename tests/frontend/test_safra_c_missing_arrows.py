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
    
    # Safra C broken setup
    house_c = areas_root / "Safra C" / "508 - Test" / ".source_files"
    house_c.mkdir(parents=True)
    state_json_c = {
        "grouped_documents": [
            {"primary_tenant": "Tenant508", "category": "letters", "dates": ["2023-01-01"], "brief_arabic_title": "Test Title 508", "vault_id": None}
        ],
        "routed_documents": [
            {"tenant": "Tenant508", "category": "letters", "dates": ["2023-01-01"], "brief_arabic_title": "Test Title 508", "vault_id": None}
        ],
        "manifest": {}
    }
    with open(house_c / "508_state.json", "w", encoding="utf-8") as f:
        json.dump(state_json_c, f)
        
    config_path = areas_root / "config.yaml"
    with open(config_path, "w") as f:
        f.write(f'inbox_path: "{areas_root}/inbox"\n')
        f.write(f'areas_root_path: "{areas_root}"\n')
        f.write('area_mappings: {}\n')
        
    env = os.environ.copy()
    env["FILE_ORGANIZER_CONFIG"] = str(config_path)
    
    process = subprocess.Popen(
        [".venv/bin/python", "-m", "uvicorn", "src.api.server:app", "--host", "127.0.0.1", "--port", "8008", "--log-level", "error"],
        env=env
    )
    time.sleep(2)
    yield "http://127.0.0.1:8008"
    process.terminate()
    process.wait()

def test_safra_c_tree_has_arrows(page: Page, mock_areas_server):
    page.goto(mock_areas_server)
    # Open Safra C
    page.click("text=Safra C")
    
    # Check that the toggle icon for 508 - Test is ▶ (which indicates it has children)
    button = page.locator("button:has-text('508 - Test')")
    expect(button.locator("span.mr-2")).to_contain_text("▶")
    
    # Click on the house to expand it
    page.click("text=508 - Test")
    
    # Check that we can see the tenant
    expect(page.locator("text=Tenant508")).to_be_visible(timeout=5000)
