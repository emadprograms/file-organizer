"""
Playwright E2E tests for Arabic House Tenancy Register & Digital Archive Profile.
Verifies:
- House-level selection (no tenant) displays 'سجل المستأجرين' by default.
- Tenancy succession cards (active occupant vs previous occupants, stay duration, doc counts).
- Digital Archive Profile (timespan, total pages, category breakdown).
- Clicking tenant card opens that tenant's categorized folders and updates title.
- Back button '← سجل المنزل' returns to the house register.
"""
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
    tmp_path = tmp_path_factory.mktemp("house_register_e2e")
    db_file = tmp_path / "organizer.db"
    areas_root = tmp_path / "areas"
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    areas_root.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn)

    # Area & House
    repo.add_area(area_id="Safra D", code="SAF D")
    repo.add_house(house_id="500", area_id="Safra D")

    # Past Tenant
    t_past = repo.add_tenant(house_id="500", name="أحمد عبدالله المطوع", start_date="2017-01-01", end_date="2019-12-31")
    # Active Tenant
    t_active = repo.add_tenant(house_id="500", name="فواز خليل الطارش", start_date="2020-01-01", end_date=None)

    # Batches
    b1 = repo.create_batch(house_id="500", filename="batch_01.pdf", file_path=str(tmp_path / "batch_01.pdf"), page_count=5)
    b2 = repo.create_batch(house_id="500", filename="batch_02.pdf", file_path=str(tmp_path / "batch_02.pdf"), page_count=10)

    # Documents
    repo.add_document(
        vault_id="v500_p1",
        house_id="500",
        tenant_id=t_past.id,
        batch_id=b1.id,
        primary_date="2017-03-15",
        arabic_title="عقد إيجار أحمد القديم",
        category="01 - عقود الإيجار",
        is_manual=0,
        page_count=3
    )
    repo.add_document(
        vault_id="v500_a1",
        house_id="500",
        tenant_id=t_active.id,
        batch_id=b2.id,
        primary_date="2020-02-10",
        arabic_title="عقد إيجار فواز الساري",
        category="01 - عقود الإيجار",
        is_manual=1,
        page_count=4
    )
    repo.add_document(
        vault_id="v500_a2",
        house_id="500",
        tenant_id=t_active.id,
        batch_id=b2.id,
        primary_date="2023-05-12",
        arabic_title="فاتورة كهرباء فواز",
        category="06 - كهرباء وماء",
        is_manual=0,
        page_count=2
    )

    v_dir = areas_root / "Safra D" / "500" / "vault"
    v_dir.mkdir(parents=True, exist_ok=True)
    (v_dir / "doc_v500_p1.pdf").write_bytes(MINIMAL_PDF)
    (v_dir / "doc_v500_a1.pdf").write_bytes(MINIMAL_PDF)
    (v_dir / "doc_v500_a2.pdf").write_bytes(MINIMAL_PDF)

    conn.close()

    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(f"""
areas_root_path: "{areas_root}"
inbox_path: "{inbox_dir}"
db_path: "{db_file}"
""")

    port = _find_free_port()
    env = {
        **subprocess.os.environ,
        "FILE_ORGANIZER_CONFIG": str(config_path),
        "FILE_ORGANIZER_DATABASE": str(db_file),
    }

    process = subprocess.Popen(
        [
            str(Path(subprocess.sys.executable).parent / "uvicorn"),
            "src.api.server:app",
            "--host", "127.0.0.1",
            "--port", str(port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 15
    started = False
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/api/tree", timeout=1) as resp:
                if resp.status == 200:
                    started = True
                    break
        except Exception:
            time.sleep(0.2)

    if not started:
        process.kill()
        raise RuntimeError("Uvicorn test server failed to start within timeout.")

    yield url

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def test_house_tenancy_register_display(page: Page, server_url: str):
    """When clicking a house (without tenant), the Arabic Tenancy Register & Archive profile loads."""
    page.goto(server_url)

    # Navigate to House 500 via tree
    page.click("text=Safra D")
    page.click("text=500")

    # Document panel is visible
    expect(page.locator("#document-list-panel")).to_be_visible()

    # Tab 1 label should be 'سجل المستأجرين'
    expect(page.locator("#tab-categories-label")).to_contain_text("سجل المستأجرين")

    # Tenancy Register displays tenant cards directly without redundant sub-header (QCK-19)
    expect(page.locator("#document-list")).not_to_contain_text("سجل المستأجرين المتعاقبين")
    expect(page.locator(".tenant-profile-card").first).to_be_visible()

    # Active Tenant card
    expect(page.locator("#document-list")).to_contain_text("فواز خليل الطارش")
    expect(page.locator("#document-list")).to_contain_text("حالي")
    expect(page.locator("#document-list")).to_contain_text("مستمر")

    # Past Tenant card
    expect(page.locator("#document-list")).to_contain_text("أحمد عبدالله المطوع")
    expect(page.locator("#document-list")).to_contain_text("سابق")
    expect(page.locator("#document-list")).to_contain_text("2017 – 2019")

    # Archive profile section removed from document-list, header export button exists
    expect(page.locator("#document-list")).not_to_contain_text("بيانات الأرشيف الرقمي للمنزل")
    expect(page.locator("#btn-export-house-archive")).to_be_visible()


def test_click_tenant_card_drills_down_to_folders(page: Page, server_url: str):
    """Clicking a tenant card opens that tenant's categorized folders and shows the back button."""
    page.goto(f"{server_url}/#/area/Safra%20D/house/500")

    # Wait for Tenancy Register
    expect(page.locator("#document-list")).to_contain_text("فواز خليل الطارش")

    # Click on Fawaz's card
    fawaz_card = page.locator(".tenant-profile-card[data-tenant-name='فواز خليل الطارش']")
    expect(fawaz_card).to_be_visible()
    fawaz_card.click()

    # URL hash updates to Fawaz
    expect(page).to_have_url(re.compile(r".*tenant.*"))

    # Header updates with tenant name and back to tenants button
    expect(page.locator("#current-house-title")).to_contain_text("500")
    expect(page.locator("#current-house-title")).to_contain_text("فواز خليل الطارش")
    back_btn = page.locator("#tab-back-to-tenants")
    expect(back_btn).to_be_visible()

    # Tab 1 changes label to Folders
    expect(page.locator("#tab-categories-label")).to_contain_text("Folders")

    # Document list now shows Fawaz's category folders
    expect(page.locator(".category-folder-card").first).to_be_visible()
    expect(page.locator("#document-list")).to_contain_text("01 - عقود الإيجار")
    expect(page.locator("#document-list")).to_contain_text("06 - كهرباء وماء")

    # Click back to tenants button
    back_btn.click()

    # Restores house register view
    expect(page.locator("#tab-categories-label")).to_contain_text("سجل المستأجرين")
    expect(page.locator("#document-list")).not_to_contain_text("سجل المستأجرين المتعاقبين")
    expect(page.locator(".tenant-profile-card").first).to_be_visible()
    expect(page.locator("#current-house-title")).to_contain_text("500")
    expect(page.locator("#btn-back-to-house-register")).to_be_hidden()
