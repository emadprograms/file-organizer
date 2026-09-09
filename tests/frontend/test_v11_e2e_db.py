"""
End-to-End Playwright UI tests against SQLite database backend for Milestone v11.0.
Verifies full feature parity:
- Tree View renders DB hierarchy with tenure subtitles and doc counts.
- Grid View mode and tenure badges (<5y emerald, 5-10y amber, >10y rose).
- Drill-down navigation to Categories and Timeline, with Back to Grid button.
- Fast SQL search modal and navigation.
- PDF serving from vault and viewing in document panel.
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
    """
    Boots a test FastAPI server pointing to a temporary SQLite database
    seeded with Safra C and houses 101 (<5y), 202 (5-10y), and 303 (>10y),
    along with vault PDFs.
    """
    tmp_path = tmp_path_factory.mktemp("v11_e2e")
    db_file = tmp_path / "organizer.db"
    areas_root = tmp_path / "areas"
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    areas_root.mkdir(parents=True, exist_ok=True)

    # 1. Initialize DB and seed data
    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn)

    # Area: Safra C
    repo.add_area(area_id="Safra C", code="SAF C")

    # Houses:
    # House 101 (<5y green tenure)
    # House 202 (5-10y yellow tenure)
    # House 303 (>10y red tenure)
    repo.add_house(house_id="101", area_id="Safra C")
    repo.add_house(house_id="202", area_id="Safra C")
    repo.add_house(house_id="303", area_id="Safra C")

    # Tenants
    t101 = repo.add_tenant(house_id="101", name="Ahmad Al-Short", start_date="2023-01-01", end_date=None)
    t202 = repo.add_tenant(house_id="202", name="Fatima Al-Medium", start_date="2017-01-01", end_date=None)
    t303 = repo.add_tenant(house_id="303", name="Khalid Al-Long", start_date="2008-01-01", end_date=None)

    # Batches
    b101 = repo.create_batch(house_id="101", filename="batch_101.pdf", file_path=str(tmp_path / "batch_101.pdf"), page_count=3)
    b202 = repo.create_batch(house_id="202", filename="batch_202.pdf", file_path=str(tmp_path / "batch_202.pdf"), page_count=2)
    b303 = repo.create_batch(house_id="303", filename="batch_303.pdf", file_path=str(tmp_path / "batch_303.pdf"), page_count=5)

    # Documents & Vault PDFs
    # House 101: 3 documents ("عقود", "كهرباء وماء")
    doc_specs_101 = [
        ("v101_1", "05 - عقود", "عقد إيجار 101", "2023-01-15"),
        ("v101_2", "06 - كهرباء وماء", "فاتورة كهرباء 101", "2023-02-15"),
        ("v101_3", "05 - عقود", "ملحق عقد 101", "2023-03-15"),
    ]
    for v_id, cat, title, p_date in doc_specs_101:
        repo.add_document(
            vault_id=v_id,
            house_id="101",
            tenant_id=t101.id,
            batch_id=b101.id,
            primary_date=p_date,
            arabic_title=title,
            category=cat,
            page_count=1
        )
        v_dir = areas_root / "Safra C" / "101" / "vault"
        v_dir.mkdir(parents=True, exist_ok=True)
        (v_dir / f"doc_{v_id}.pdf").write_bytes(MINIMAL_PDF)

    # House 202: 2 documents
    doc_specs_202 = [
        ("v202_1", "05 - عقود", "عقد إيجار 202", "2017-02-01"),
        ("v202_2", "06 - كهرباء وماء", "فاتورة ماء 202", "2017-05-01"),
    ]
    for v_id, cat, title, p_date in doc_specs_202:
        repo.add_document(
            vault_id=v_id,
            house_id="202",
            tenant_id=t202.id,
            batch_id=b202.id,
            primary_date=p_date,
            arabic_title=title,
            category=cat,
            page_count=1
        )
        v_dir = areas_root / "Safra C" / "202" / "vault"
        v_dir.mkdir(parents=True, exist_ok=True)
        (v_dir / f"doc_{v_id}.pdf").write_bytes(MINIMAL_PDF)

    # House 303: 5 documents
    doc_specs_303 = [
        ("v303_1", "05 - عقود", "عقد إيجار قديم 303", "2008-01-15"),
        ("v303_2", "05 - عقود", "تجديد عقد 303", "2012-01-15"),
        ("v303_3", "06 - كهرباء وماء", "فاتورة كهرباء قديمة 303", "2015-06-01"),
        ("v303_4", "06 - كهرباء وماء", "فاتورة بلدية 303", "2018-09-01"),
        ("v303_5", "03 - أمر تخصيص", "أمر تخصيص 303", "2008-01-01"),
    ]
    for v_id, cat, title, p_date in doc_specs_303:
        repo.add_document(
            vault_id=v_id,
            house_id="303",
            tenant_id=t303.id,
            batch_id=b303.id,
            primary_date=p_date,
            arabic_title=title,
            category=cat,
            page_count=1
        )
        v_dir = areas_root / "Safra C" / "303" / "vault"
        v_dir.mkdir(parents=True, exist_ok=True)
        (v_dir / f"doc_{v_id}.pdf").write_bytes(MINIMAL_PDF)

    # Add searchable pages
    repo.add_pages_bulk([
        {
            "batch_id": b101.id,
            "page_number": 1,
            "house_id": "101",
            "vault_id": "v101_1",
            "category": "05 - عقود",
            "content_explanation": "شروط عقد الإيجار للمنزل 101 والمستأجر أحمد",
            "subject": "عقد إيجار 101",
        },
        {
            "batch_id": b101.id,
            "page_number": 2,
            "house_id": "101",
            "vault_id": "v101_2",
            "category": "06 - كهرباء وماء",
            "content_explanation": "فاتورة استهلاك الكهرباء والماء لشهر فبراير",
            "subject": "فاتورة كهرباء 101",
        },
    ])

    conn.close()

    # 2. Write config.yaml
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(f'inbox_path: "{inbox_dir}"\n')
        f.write(f'areas_root_path: "{areas_root}"\n')
        f.write(f'db_path: "{db_file}"\n')
        f.write('area_mappings:\n')
        f.write('  "Safra C": "SAF C"\n')

    # 3. Boot FastAPI server via uvicorn
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

    # Poll server until ready
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


def test_tree_view_renders_db_hierarchy(page: Page, server_url: str):
    """Verifies areas and houses render from DB with tenure badges and tenant overview."""
    page.goto(server_url)

    # Verify Areas section header
    expect(page.locator("#sidebar-section-title")).to_have_text("Areas")

    # Safra C is visible in the sidebar
    area_btn = page.locator(".area-grid-btn:has-text('Safra C')")
    expect(area_btn).to_be_visible()

    # Click Safra C
    area_btn.click()

    # Houses 101, 202, 303 appear as cards in area grid
    card_101 = page.locator('.house-card[data-house-id="101"]')
    card_202 = page.locator('.house-card[data-house-id="202"]')
    card_303 = page.locator('.house-card[data-house-id="303"]')

    expect(card_101).to_be_visible()
    expect(card_202).to_be_visible()
    expect(card_303).to_be_visible()

    # Verify tenure badges & colors:
    expect(card_101).to_have_class(re.compile(r"border-l-emerald-500"))
    expect(card_101.locator(".tenure-badge")).to_contain_text("< 5 Yrs")

    expect(card_202).to_have_class(re.compile(r"border-l-amber-500"))
    expect(card_202.locator(".tenure-badge")).to_contain_text("5–10 Yrs")

    expect(card_303).to_have_class(re.compile(r"border-l-rose-500"))
    expect(card_303.locator(".tenure-badge")).to_contain_text("> 10 Yrs")


def test_grid_view_mode_and_tenure_badges(page: Page, server_url: str):
    """Verifies house cards with tenure color-coding, doc counts, and tenants overview."""
    page.goto(server_url)

    expect(page.locator("#sidebar-section-title")).to_have_text("Areas")

    # Click Safra C area in sidebar
    page.click(".area-grid-btn:has-text('Safra C')")

    # Verify house cards render in #area-grid-container
    expect(page.locator("#area-grid-panel")).to_be_visible()
    expect(page.locator("#area-grid-container .house-card")).to_have_count(3)

    # Verify tenure badges & colors:
    # House 101: < 5 years -> Green styling & badge, 3 docs
    card_101 = page.locator('.house-card[data-house-id="101"]')
    expect(card_101).to_have_class(re.compile(r"border-l-emerald-500"))
    expect(card_101.locator(".tenure-badge")).to_contain_text("< 5 Yrs")
    expect(card_101.locator(".doc-count")).to_contain_text("3 Docs")
    expect(card_101.locator(".tenant-name")).to_contain_text("Ahmad Al-Short")

    # House 202: 5-10 years -> Yellow styling & badge, 2 docs
    card_202 = page.locator('.house-card[data-house-id="202"]')
    expect(card_202).to_have_class(re.compile(r"border-l-amber-500"))
    expect(card_202.locator(".tenure-badge")).to_contain_text("5–10 Yrs")
    expect(card_202.locator(".doc-count")).to_contain_text("2 Docs")
    expect(card_202.locator(".tenant-name")).to_contain_text("Fatima Al-Medium")

    # House 303: > 10 years -> Red styling & badge, 5 docs
    card_303 = page.locator('.house-card[data-house-id="303"]')
    expect(card_303).to_have_class(re.compile(r"border-l-rose-500"))
    expect(card_303.locator(".tenure-badge")).to_contain_text("> 10 Yrs")
    expect(card_303.locator(".doc-count")).to_contain_text("5 Docs")
    expect(card_303.locator(".tenant-name")).to_contain_text("Khalid Al-Long")


def test_drill_down_navigation_to_categories_and_timeline(page: Page, server_url: str):
    """Clicking house card in houses overview opens categories and timeline, and Back returns."""
    page.goto(server_url)

    # Select Safra C
    page.click(".area-grid-btn:has-text('Safra C')")

    # Click House 101 card
    page.click('.house-card[data-house-id="101"]')

    # Grid panel hidden, document list panel visible
    expect(page.locator("#area-grid-panel")).to_be_hidden()
    expect(page.locator("#document-list-panel")).to_be_visible()
    expect(page.locator("#current-house-title")).to_contain_text("101")

    # Tenancy Register shows Ahmad Al-Short
    expect(page.locator("#document-list")).to_contain_text("Ahmad Al-Short")

    # Drill down into tenant categories by clicking tenant profile card
    page.click(".tenant-profile-card")
    expect(page.locator("#document-list")).to_contain_text("عقود")
    expect(page.locator("#document-list")).to_contain_text("كهرباء وماء")

    # Switch to Timeline tab
    page.click("#tab-timeline")
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار 101")
    expect(page.locator("#document-list")).to_contain_text("فاتورة كهرباء 101")

    # Back to Area Houses button and Back to Tenants button are visible
    back_btn = page.locator("#back-to-grid-btn")
    expect(back_btn).to_be_visible()
    expect(back_btn).to_contain_text("Safra C Houses")
    expect(page.locator("#tab-back-to-tenants")).to_be_visible()

    # Click Back button
    back_btn.click()

    # Returns to Area Houses View
    expect(page.locator("#area-grid-panel")).to_be_visible()
    expect(page.locator("#document-list-panel")).to_be_hidden()
    expect(back_btn).to_be_hidden()


def test_search_modal_and_results(page: Page, server_url: str):
    """Search shortcut or typing finds house and document records from DB."""
    page.goto(server_url)

    # Shortcut Cmd+K / Ctrl+K focuses search
    page.keyboard.press("ControlOrMeta+K")
    search_input = page.locator("#search-input")
    expect(search_input).to_be_focused()

    # Search for house 101
    search_input.fill("101")

    search_results = page.locator("#search-results")
    expect(search_results).to_be_visible()
    expect(search_results).to_contain_text("101")

    # Click house 101 result
    page.click("#search-results a:has-text('101')")

    # Should navigate and open house 101
    expect(page).to_have_url(re.compile(r".*#/area/Safra.*C/house/101"))
    expect(search_results).to_be_hidden()
    expect(page.locator("#document-list-panel")).to_be_visible()
    expect(page.locator("#current-house-title")).to_contain_text("101")


def test_pdf_serving_and_modal(page: Page, server_url: str):
    """Clicking document opens PDF viewer with valid vault PDF served from DB backend."""
    page.goto(f"{server_url}/#/area/Safra%20C/house/101")

    expect(page.locator("#document-list-panel")).to_be_visible()

    # House level shows Tenancy Register; click tenant card to drill down into folders
    page.locator(".tenant-profile-card").first.click()

    # Expand category '05 - عقود' / 'عقود'
    cat_card = page.locator(".category-folder-card:has-text('عقود')").first
    cat_card.click()

    # Click on the document link
    doc_link = page.locator("#document-list div:has-text('عقد إيجار 101')").last
    expect(doc_link).to_be_visible()
    doc_link.click()

    # Document viewer panel opens
    viewer_panel = page.locator("#document-viewer-panel")
    expect(viewer_panel).to_be_visible()
    expect(page.locator("#viewer-title")).to_contain_text("عقد إيجار 101")

    # Verify iframe src points to the PDF endpoint
    pdf_frame = page.locator("#pdf-frame")
    expect(pdf_frame).to_be_visible()
    src = pdf_frame.get_attribute("src")
    assert "v101_1" in src
    assert "Safra%20C" in src or "Safra C" in src
    assert "101" in src

    # Verify direct HTTP PDF request returns valid 200 PDF response
    response = page.request.get(f"{server_url}/api/areas/Safra%20C/houses/101/pdf/v101_1")
    assert response.status == 200
    assert response.headers.get("content-type") == "application/pdf"
    assert response.body().startswith(b"%PDF-")


def test_tenant_management_modal_e2e(page: Page, server_url: str):
    """Opens Manage Tenants modal, inspects existing tenant, adds a new tenant, saves, and verifies."""
    page.goto(f"{server_url}/#/area/Safra%20C/house/101")

    expect(page.locator("#document-list-panel")).to_be_visible()

    # Manage Tenants button in doc list tabs
    manage_btn = page.locator("#btn-manage-tenants")
    expect(manage_btn).to_be_visible()
    manage_btn.click()

    # Modal appears
    modal = page.locator("#tenant-modal")
    expect(modal).to_be_visible()
    expect(page.locator("#tenant-modal-title")).to_contain_text("Manage Tenants: 101 (Safra C)")

    # Wait for rows to load
    tenant_name_inputs = page.locator(".tenant-name-input")
    expect(tenant_name_inputs.first).to_have_value("Ahmad Al-Short")

    # Add a second tenant row
    page.click("#btn-add-tenant-row")
    expect(page.locator(".tenant-row")).to_have_count(2)

    # Fill new tenant
    page.locator(".tenant-name-input").nth(1).fill("New Tenant Test")
    page.locator(".tenant-start-input").nth(1).fill("2024-01-01")

    # Click Save & Reallocate
    save_btn = page.locator("#tenant-modal-save")
    save_btn.click()

    # Modal should close after saving
    expect(modal).to_be_hidden()


def test_tenant_modal_present_checkbox_toggle(page: Page, server_url: str):
    """Toggling Present checkbox disables/enables end date input and clears value."""
    page.goto(f"{server_url}/#/area/Safra%20C/house/101")
    expect(page.locator("#document-list-panel")).to_be_visible()

    # Open modal
    page.locator("#btn-manage-tenants").click()
    modal = page.locator("#tenant-modal")
    expect(modal).to_be_visible()

    # Ahmad is currently Present (no end date)
    present_chk = page.locator(".tenant-present-check").first
    end_input = page.locator(".tenant-end-input").first
    expect(present_chk).to_be_checked()
    expect(end_input).to_be_disabled()

    # Uncheck Present -> should enable end date
    present_chk.uncheck()
    expect(end_input).to_be_enabled()
    end_input.fill("2023-12-31")
    expect(end_input).to_have_value("2023-12-31")

    # Re-check Present -> should clear and disable end date
    present_chk.check()
    expect(end_input).to_be_disabled()
    expect(end_input).to_have_value("")

    # Cancel modal
    page.locator("#tenant-modal-cancel").click()
    expect(modal).to_be_hidden()


def test_viewer_manual_tenant_override_e2e(page: Page, server_url: str):
    """Document viewer shows tenant dropdown allowing manual assignment."""
    page.goto(f"{server_url}/#/area/Safra%20C/house/101/tenant/101_Ahmad%20Al-Short")
    expect(page.locator("#document-list-panel")).to_be_visible()

    # Open category and document
    page.locator(".category-folder-card:has-text('عقود')").first.click()
    doc_link = page.locator("#document-list div:has-text('عقد إيجار 101')").last
    expect(doc_link).to_be_visible()
    doc_link.click()

    # Viewer opens
    expect(page.locator("#document-viewer-panel")).to_be_visible()

    # Tenant selector is visible with options
    tenant_select = page.locator("#viewer-tenant-select")
    expect(tenant_select).to_be_visible()
    expect(tenant_select.locator("option")).not_to_have_count(0)


def test_document_action_modal_rename_and_lock_badge_e2e(page: Page, server_url: str):
    """Renaming document via action modal updates title and shows manual lock indicator."""
    page.goto(f"{server_url}/#/area/Safra%20C/house/101/tenant/101_Ahmad%20Al-Short")
    expect(page.locator("#document-list-panel")).to_be_visible()

    # Expand category '05 - عقود'
    page.locator(".category-folder-card:has-text('عقود')").first.click()

    # Click document action button (...) using data-vault-id
    menu_btn = page.locator(".doc-menu-btn[data-vault-id='v101_1']")
    expect(menu_btn).to_be_attached()
    menu_btn.click(force=True)

    # Modal appears
    modal = page.locator("#doc-action-modal")
    expect(modal).to_be_visible()
    expect(page.locator("#doc-modal-arabic-title")).to_have_value("عقد إيجار 101")

    # Rename title
    page.locator("#doc-modal-arabic-title").fill("عقد إيجار محدث 101")
    page.locator("#doc-modal-submit").click()

    # Modal closes after save
    expect(modal).to_be_hidden()

    # Verify updated title in category list
    page.locator(".category-folder-card:has-text('عقود')").first.click()
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار محدث 101")
    expect(page.locator("#document-list")).to_contain_text("🔒")


def test_document_action_modal_custom_folder_e2e(page: Page, server_url: str):
    """Creating a custom folder in the modal assigns next sequential folder number (14)."""
    page.goto(f"{server_url}/#/area/Safra%20C/house/101/tenant/101_Ahmad%20Al-Short")
    expect(page.locator("#document-list-panel")).to_be_visible()

    # Open 'كهرباء وماء'
    page.locator(".category-folder-card:has-text('كهرباء وماء')").first.click()

    # Open menu
    menu_btn = page.locator(".doc-menu-btn[data-vault-id='v101_2']")
    expect(menu_btn).to_be_attached()
    menu_btn.click(force=True)

    modal = page.locator("#doc-action-modal")
    expect(modal).to_be_visible()

    # Select '+ Create New Folder...'
    page.locator("#doc-modal-folder-select").select_option("__NEW_CUSTOM_FOLDER__")
    custom_container = page.locator("#doc-custom-folder-container")
    expect(custom_container).to_be_visible()

    # Enter custom folder name
    page.locator("#doc-custom-folder-input").fill("مستندات بنكية جديدة")
    page.locator("#doc-modal-submit").click()

    expect(modal).to_be_hidden()

    # Verify new category card exists with prefix 14
    new_cat = page.locator(".category-folder-card:has-text('14 - مستندات بنكية جديدة')").first
    expect(new_cat).to_be_visible()


def test_document_action_modal_copy_e2e(page: Page, server_url: str):
    """Copying a document duplicates it into target folder while preserving original."""
    page.goto(f"{server_url}/#/area/Safra%20C/house/101/tenant/101_Ahmad%20Al-Short")
    expect(page.locator("#document-list-panel")).to_be_visible()

    # Open '05 - عقود'
    page.locator(".category-folder-card:has-text('عقود')").first.click()

    # Open modal on v101_3
    menu_btn = page.locator(".doc-menu-btn[data-vault-id='v101_3']")
    expect(menu_btn).to_be_attached()
    menu_btn.click(force=True)

    modal = page.locator("#doc-action-modal")
    expect(modal).to_be_visible()

    # Switch to Copy mode
    copy_mode_btn = page.locator("#btn-mode-copy")
    copy_mode_btn.click()
    expect(copy_mode_btn).to_have_class(re.compile(r".*bg-white.*text-blue-600.*"))

    # Select '06 - كهرباء وماء'
    page.locator("#doc-modal-folder-select").select_option("06 - كهرباء وماء")
    page.locator("#doc-modal-submit").click()

    expect(modal).to_be_hidden()

    # Check that original document still exists in '05 - عقود'
    page.locator(".category-folder-card:has-text('عقود')").first.click()
    expect(page.locator("#document-list")).to_contain_text("ملحق عقد 101")

    # Check that copy exists in '06 - كهرباء وماء'
    page.locator(".category-folder-card:has-text('كهرباء وماء')").first.click()
    expect(page.locator("#document-list")).to_contain_text("ملحق عقد 101")


def test_document_action_modal_reset_lock_e2e(page: Page, server_url: str):
    """Manual lock banner is displayed for locked docs and can be reset."""
    # Ensure v101_1 is locked so test is self-contained
    resp = page.request.patch(
        f"{server_url}/api/areas/Safra%20C/houses/101/documents/v101_1",
        data={"is_manual": 1, "category": "05 - عقود", "arabic_title": "عقد إيجار 101"}
    )
    assert resp.status == 200

    page.goto(f"{server_url}/#/area/Safra%20C/house/101/tenant/101_Ahmad%20Al-Short")
    expect(page.locator("#document-list-panel")).to_be_visible()

    # Open 'عقود'
    page.locator(".category-folder-card:has-text('عقود')").first.click()

    # Open menu for v101_1
    menu_btn = page.locator(".doc-menu-btn[data-vault-id='v101_1']")
    expect(menu_btn).to_be_attached()
    menu_btn.click(force=True)

    modal = page.locator("#doc-action-modal")
    expect(modal).to_be_visible()

    # Verify manual lock banner is shown
    banner = page.locator("#doc-manual-banner")
    expect(banner).to_be_visible()
    expect(banner).to_contain_text("Manually Assigned")

    # Click Reset to Auto
    reset_btn = page.locator("#btn-doc-reset-lock")
    reset_btn.click()

    # Modal closes after reset
    expect(modal).to_be_hidden()


def test_timeline_view_doc_action_menu_e2e(page: Page, server_url: str):
    """Timeline view documents show action menu button that opens the modal."""
    page.goto(f"{server_url}/#/area/Safra%20C/house/101")
    expect(page.locator("#document-list-panel")).to_be_visible()

    # Switch to Timeline tab
    page.locator("#tab-timeline").click()

    # Find timeline doc menu button
    timeline_menu_btn = page.locator(".doc-menu-btn[data-vault-id='v101_1']")
    expect(timeline_menu_btn).to_be_attached()
    timeline_menu_btn.click(force=True)

    # Modal opens
    modal = page.locator("#doc-action-modal")
    expect(modal).to_be_visible()

    # Cancel closes modal
    page.locator("#doc-modal-cancel").click()
    expect(modal).to_be_hidden()



