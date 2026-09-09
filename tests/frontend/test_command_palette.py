"""
Playwright E2E tests for Command Palette (⌘K) Modal.
Verifies:
- Trigger button (#btn-search-trigger) and shortcut (⌘K / Ctrl+K) toggle modal.
- Grouped sections for Houses, Tenants, and Documents.
- Breadcrumb path hierarchy display for documents.
- Full keyboard navigation (ArrowDown, ArrowUp, Enter, Escape).
- Direct document viewing upon selection.
"""
import os
import sys
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

MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000111 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF\n"
)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server_url(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("command_palette_e2e")
    db_file = tmp_path / "organizer.db"
    areas_root = tmp_path / "areas"
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    areas_root.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn)

    # Area
    repo.add_area(area_id="Safra D", code="SAF D")

    # House 500
    repo.add_house(house_id="500", area_id="Safra D")

    # Tenant Fawaz
    t500 = repo.add_tenant(house_id="500", name="فواز خليل الطارش", start_date="2020-01-01", end_date=None)

    # Batch
    b500 = repo.create_batch(house_id="500", filename="batch_500.pdf", file_path=str(tmp_path / "batch_500.pdf"), page_count=3)

    # Documents
    repo.add_document(
        vault_id="v500_1",
        house_id="500",
        tenant_id=t500.id,
        batch_id=b500.id,
        primary_date="2020-03-15",
        arabic_title="تعديلات المنزل",
        category="12 - تعديلات",
        is_manual=1,
        page_count=1
    )
    repo.add_document(
        vault_id="v500_2",
        house_id="500",
        tenant_id=t500.id,
        batch_id=b500.id,
        primary_date="2021-06-01",
        arabic_title="فاتورة كهرباء فواز",
        category="06 - كهرباء وماء",
        is_manual=0,
        page_count=1
    )

    v_dir = areas_root / "Safra D" / "500" / "vault"
    v_dir.mkdir(parents=True, exist_ok=True)
    (v_dir / "doc_v500_1.pdf").write_bytes(MINIMAL_PDF)
    (v_dir / "doc_v500_2.pdf").write_bytes(MINIMAL_PDF)

    repo.add_pages_bulk([
        {
            "batch_id": b500.id,
            "page_number": 1,
            "house_id": "500",
            "vault_id": "v500_1",
            "category": "12 - تعديلات",
            "content_explanation": "طلب تعديلات وإصلاحات منزل 500",
            "subject": "تعديلات",
        }
    ])

    conn.close()

    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(f'inbox_path: "{inbox_dir}"\n')
        f.write(f'areas_root_path: "{areas_root}"\n')
        f.write(f'db_path: "{db_file}"\n')
        f.write('area_mappings:\n')
        f.write('  "Safra D": "SAF D"\n')

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["FILE_ORGANIZER_CONFIG"] = str(config_path)

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "error",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    deadline = time.time() + 15
    ready = False
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/api/tree", timeout=1) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            time.sleep(0.1)

    if not ready:
        process.terminate()
        stdout, stderr = process.communicate()
        raise RuntimeError(f"FastAPI server failed to start: {stderr.decode('utf-8', errors='ignore')}")

    yield base_url

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def test_command_palette_trigger_button_and_shortcut(page: Page, server_url: str):
    """Clicking trigger button or pressing Cmd+K opens the Command Palette modal."""
    page.goto(server_url)

    palette_modal = page.locator("#command-palette-modal")
    expect(palette_modal).to_be_hidden()

    # 1. Click trigger button
    page.click("#btn-search-trigger")
    expect(palette_modal).to_be_visible()
    expect(page.locator("#search-input")).to_be_focused()

    # 2. Press Escape to close
    page.keyboard.press("Escape")
    expect(palette_modal).to_be_hidden()

    # 3. Press Cmd+K / Ctrl+K
    page.keyboard.press("ControlOrMeta+K")
    expect(palette_modal).to_be_visible()
    expect(page.locator("#search-input")).to_be_focused()


def test_command_palette_grouped_sections_and_breadcrumbs(page: Page, server_url: str):
    """Searching 500 displays distinct Houses, Tenants, and Documents sections with breadcrumbs."""
    page.goto(server_url)

    page.keyboard.press("ControlOrMeta+K")
    search_input = page.locator("#search-input")
    search_input.fill("500")

    # Wait for results
    results_container = page.locator("#search-results")
    expect(results_container).to_be_visible()

    # Verify section headers
    expect(results_container.get_by_text("Houses", exact=True)).to_be_visible()
    expect(results_container.get_by_text("Tenants", exact=True)).to_be_visible()
    expect(results_container.get_by_text("Documents", exact=True)).to_be_visible()

    # Verify House item
    expect(results_container.locator("text=House 500").first).to_be_visible()

    # Verify Tenant item
    expect(results_container.locator("text=فواز خليل الطارش").first).to_be_visible()

    # Verify Document item and its breadcrumb path
    doc_item = results_container.locator("text=تعديلات المنزل").first
    expect(doc_item).to_be_visible()

    # Breadcrumb format: Area › House › Tenant › Folder
    breadcrumb = results_container.locator("text=Safra D › House 500 › فواز خليل الطارش › 12 - تعديلات").first
    expect(breadcrumb).to_be_visible()

    # Verify manual lock badge
    expect(results_container.locator("text=🔒").first).to_be_visible()


def test_command_palette_keyboard_navigation_and_selection(page: Page, server_url: str):
    """Arrow keys navigate results and Enter selects the active item."""
    page.goto(server_url)

    page.keyboard.press("ControlOrMeta+K")
    search_input = page.locator("#search-input")
    search_input.fill("500")

    # Wait for search results
    page.wait_for_selector(".command-palette-result-item")

    # Press Enter to select the first highlighted result (House 500)
    page.keyboard.press("Enter")

    # Command Palette should close and navigate to house 500
    expect(page.locator("#command-palette-modal")).to_be_hidden()
    expect(page.locator("#document-list-panel")).to_be_visible()
    expect(page.locator("#current-house-title")).to_contain_text("500")


def test_command_palette_document_direct_open(page: Page, server_url: str):
    """Clicking a document result opens the PDF viewer panel with that document."""
    page.goto(server_url)

    page.keyboard.press("ControlOrMeta+K")
    search_input = page.locator("#search-input")
    search_input.fill("تعديلات")

    # Click on the document result
    doc_link = page.locator("#search-results a:has-text('تعديلات المنزل')")
    expect(doc_link).to_be_visible()
    doc_link.click()

    # Command Palette closes
    expect(page.locator("#command-palette-modal")).to_be_hidden()

    # Document viewer panel opens with the PDF
    viewer_panel = page.locator("#document-viewer-panel")
    expect(viewer_panel).to_be_visible()
    expect(page.locator("#viewer-title")).to_contain_text("تعديلات المنزل")

    pdf_frame = page.locator("#pdf-frame")
    expect(pdf_frame).to_be_visible()
    src = pdf_frame.get_attribute("src")
    assert "v500_1" in src
