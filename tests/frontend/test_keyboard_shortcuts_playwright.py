"""
Playwright E2E tests for Keyboard Shortcuts Helper Modal (Phase 108).
Verifies:
- Trigger button (#btn-shortcuts-trigger) opens the modal.
- Global '?' key opens the modal.
- Close button (#shortcuts-modal-close) and Escape dismiss the modal.
- Typing '?' inside an input field does not trigger the modal.
"""
import os
import sys
import re
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
import pytest
from playwright.sync_api import Page, expect

from src.db.connection import get_db_connection
from src.db.schema import init_db
from src.db.repository import Repository


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server_url(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("shortcuts_e2e")
    db_file = tmp_path / "organizer.db"
    areas_root = tmp_path / "areas"
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    areas_root.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn)
    repo.add_area(area_id="Safra C", code="SAF C")
    repo.add_house(house_id="101", area_id="Safra C")
    repo.add_tenant(house_id="101", name="محمد السعيد", start_date="2023-01-01", end_date=None)
    conn.close()

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f'db_path: "{db_file}"\n'
        f'areas_root_path: "{areas_root}"\n'
        f'inbox_path: "{inbox_dir}"\n',
        encoding="utf-8"
    )

    port = _find_free_port()
    env = os.environ.copy()
    env["FILE_ORGANIZER_CONFIG"] = str(config_path)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api.server:app", "--host", "127.0.0.1", "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 10
    started = False
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/api/tree", timeout=1) as resp:
                if resp.status == 200:
                    started = True
                    break
        except Exception:
            time.sleep(0.1)

    if not started:
        proc.kill()
        pytest.fail("FastAPI server failed to start within 10 seconds")

    yield url

    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_keyboard_shortcuts_trigger_and_modal_display(page: Page, server_url: str):
    page.goto(server_url)
    page.wait_for_selector("#btn-shortcuts-trigger")

    modal = page.locator("#keyboard-shortcuts-modal")
    expect(modal).to_have_class(re.compile(r"\bhidden\b"))

    # 1. Click the navbar trigger button
    page.click("#btn-shortcuts-trigger")
    expect(modal).not_to_have_class(re.compile(r"\bhidden\b"))
    expect(page.locator("#shortcuts-modal-title")).to_contain_text("Keyboard Shortcuts")
    expect(modal).to_contain_text("⌘K")
    expect(modal).to_contain_text("⌘I")
    expect(modal).to_contain_text("Space")

    # 2. Dismiss via close button
    page.click("#shortcuts-modal-close")
    expect(modal).to_have_class(re.compile(r"\bhidden\b"))

    # 3. Open via '?' key
    page.keyboard.press("?")
    expect(modal).not_to_have_class(re.compile(r"\bhidden\b"))

    # 4. Dismiss via Escape key
    page.keyboard.press("Escape")
    expect(modal).to_have_class(re.compile(r"\bhidden\b"))


def test_keyboard_shortcuts_isolated_from_input_fields(page: Page, server_url: str):
    page.goto(server_url)
    page.wait_for_selector("#btn-search-trigger")

    # Open spotlight palette
    page.click("#btn-search-trigger")
    search_input = page.locator("#search-input")
    expect(search_input).to_be_visible()

    # Typing '?' in the search input should NOT trigger the shortcuts modal
    search_input.type("?")
    shortcuts_modal = page.locator("#keyboard-shortcuts-modal")
    expect(shortcuts_modal).to_have_class(re.compile(r"\bhidden\b"))

    # Close palette
    page.keyboard.press("Escape")
    expect(page.locator("#command-palette-modal")).to_have_class(re.compile(r"\bhidden\b"))
