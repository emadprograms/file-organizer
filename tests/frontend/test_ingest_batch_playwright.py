"""
Playwright E2E tests for Ingest Station 3-Section Modes, Direct Drag-and-Drop, and AI removal.
"""

import json
import re
from pathlib import Path
import pytest
from playwright.sync_api import Page, expect

HTML = Path(__file__).parent.parent.parent / "src" / "api" / "static" / "index.html"

TREE_DATA = [
    {
        "id": "area_Safra_C",
        "name": "Safra C",
        "type": "area",
        "children": [
            {
                "id": "514",
                "name": "514",
                "type": "house",
                "children": [
                    {
                        "id": "1",
                        "name": "محمد مبارك الشمري",
                        "type": "tenant",
                        "start_date": "2020-01-01",
                        "end_date": None,
                        "children": None,
                    }
                ],
            },
            {
                "id": "515",
                "name": "515",
                "type": "house",
                "children": [
                    {
                        "id": "2",
                        "name": "علي حسن أحمد",
                        "type": "tenant",
                        "start_date": "2021-01-01",
                        "end_date": None,
                        "children": None,
                    }
                ],
            },
        ],
    }
]


def _setup_ingest_routes(page: Page, ingest_calls: list = None):
    """Setup mock API routes for Ingest Station tests."""
    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text(encoding="utf-8")
    ))

    page.route("http://localhost:9999/api/tree", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps(TREE_DATA)
    ))

    page.route(re.compile(r".*/api/areas/.*/houses/.*/tenants"), lambda r: r.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([{"id": 1, "name": "محمد مبارك الشمري", "start_date": "2020-01-01", "end_date": None}])
    ))

    page.route(re.compile(r".*/api/areas/.*/houses/.*/categories"), lambda r: r.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([
            {"name": "05 - عقود", "document_count": 1, "documents": []},
            {"name": "13 - رسائل متنوعة", "document_count": 0, "documents": []}
        ])
    ))

    def handle_ingest(route):
        if route.request.method == "POST":
            post_data = route.request.post_data_buffer
            headers = route.request.headers
            if ingest_calls is not None:
                ingest_calls.append({
                    "url": route.request.url,
                    "method": route.request.method,
                    "post_data_len": len(post_data) if post_data else 0,
                    "content_type": headers.get("content-type", ""),
                })
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"status": "success", "vault_id": f"v-{len(ingest_calls or [])}"}),
            )
        else:
            route.continue_()

    page.route("http://localhost:9999/api/ingest", handle_ingest)


def test_ingest_station_modal_has_no_ai_features(page: Page):
    """Ensure #btn-ingest-autofill and any AI references are completely absent."""
    _setup_ingest_routes(page)
    page.goto("http://localhost:9999/")

    # Open modal
    page.click("#btn-ingest-trigger")
    expect(page.locator("#ingest-station-modal")).to_be_visible()

    # Verify AI button does NOT exist anywhere in DOM
    expect(page.locator("#btn-ingest-autofill")).to_have_count(0)

    # Verify no AI preview container or text in the modal
    modal_text = page.locator("#ingest-station-modal").inner_text()
    assert "Autofill with AI" not in modal_text
    assert "AI Suggestions" not in modal_text
    assert "AI Category" not in modal_text


def test_ingest_station_mode_switch(page: Page):
    """Verify 3-tab segmented navigation bar switching."""
    _setup_ingest_routes(page)
    page.goto("http://localhost:9999/")

    page.click("#btn-ingest-trigger")
    expect(page.locator("#ingest-station-modal")).to_be_visible()

    # Single Document default
    expect(page.locator("#section-mode-single")).to_be_visible()
    expect(page.locator("#section-mode-broadcast")).to_be_hidden()
    expect(page.locator("#section-mode-housebatch")).to_be_hidden()
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Ingest Document")

    # Switch to Broadcast Notice
    page.click("#tab-mode-broadcast")
    expect(page.locator("#section-mode-single")).to_be_hidden()
    expect(page.locator("#section-mode-broadcast")).to_be_visible()
    expect(page.locator("#section-mode-housebatch")).to_be_hidden()
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Broadcast to 0 Houses")

    # Switch to House Batch
    page.click("#tab-mode-housebatch")
    expect(page.locator("#section-mode-single")).to_be_hidden()
    expect(page.locator("#section-mode-broadcast")).to_be_hidden()
    expect(page.locator("#section-mode-housebatch")).to_be_visible()
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Ingest 0 Documents")

    # Switch back to Single Document
    page.click("#tab-mode-single")
    expect(page.locator("#section-mode-single")).to_be_visible()
    expect(page.locator("#section-mode-broadcast")).to_be_hidden()
    expect(page.locator("#section-mode-housebatch")).to_be_hidden()
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Ingest Document")


def test_house_batch_queue_population_and_submit(page: Page, tmp_path):
    """Verify uploading multiple files in House Batch mode renders queue and submits sequentially."""
    ingest_calls = []
    _setup_ingest_routes(page, ingest_calls=ingest_calls)

    # Create two temporary test PDF files
    pdf1 = tmp_path / "bill_house_514.pdf"
    pdf1.write_bytes(b"%PDF-1.4 sample bill 514")
    pdf2 = tmp_path / "contract_514.pdf"
    pdf2.write_bytes(b"%PDF-1.4 sample contract 514")

    page.goto("http://localhost:9999/")
    page.click("#btn-ingest-trigger")
    expect(page.locator("#ingest-station-modal")).to_be_visible()

    # Switch to House Batch tab
    page.click("#tab-mode-housebatch")
    expect(page.locator("#section-mode-housebatch")).to_be_visible()

    # Select House
    page.select_option("#housebatch-house-select", "514")

    # Upload two files into housebatch-file-input
    page.set_input_files("#housebatch-file-input", [str(pdf1), str(pdf2)])

    # Check badge and submit button text
    expect(page.locator("#housebatch-count-badge")).to_have_text("2 files")
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Ingest 2 Documents")

    # Check that 2 file items exist in list
    file_items = page.locator(".housebatch-file-row")
    expect(file_items).to_have_count(2)

    # Select shared category
    page.select_option("#housebatch-category-select", "06 - كهرباء وماء")

    # Click Submit
    page.click("#btn-ingest-submit")

    # Modal should close on completion
    expect(page.locator("#ingest-station-modal")).to_be_hidden()

    # Verify both requests were posted
    assert len(ingest_calls) == 2


def test_broadcast_document_to_multiple_houses(page: Page, tmp_path):
    """Verify broadcasting a single document to multiple houses in Broadcast Notice tab."""
    ingest_calls = []
    _setup_ingest_routes(page, ingest_calls=ingest_calls)

    notice_pdf = tmp_path / "general_municipality_notice.pdf"
    notice_pdf.write_bytes(b"%PDF-1.4 municipality notice")

    page.goto("http://localhost:9999/")
    page.click("#btn-ingest-trigger")
    expect(page.locator("#ingest-station-modal")).to_be_visible()

    # Switch to Broadcast Notice tab
    page.click("#tab-mode-broadcast")
    expect(page.locator("#section-mode-broadcast")).to_be_visible()

    # Upload single notice PDF
    page.set_input_files("#broadcast-file-input", [str(notice_pdf)])

    # Verify title was auto-filled
    expect(page.locator("#broadcast-title-input")).to_have_value("general municipality notice")

    # Select Area to populate houses checklist
    page.select_option("#broadcast-area-select", "Safra C")

    # Check that houses are rendered in checklist
    items = page.locator(".broadcast-house-item")
    expect(items).to_have_count(2)

    # Click Select All
    page.click("#btn-broadcast-select-all")
    expect(page.locator("#broadcast-selected-count")).to_have_text("2 selected")
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Broadcast to 2 Houses")

    # Select category
    page.select_option("#broadcast-category-select", "09 - إشعارات")

    # Submit
    page.click("#btn-ingest-submit")

    # Modal closes and 2 ingest calls made for the 2 houses
    expect(page.locator("#ingest-station-modal")).to_be_hidden()
    assert len(ingest_calls) == 2


def test_direct_drag_drop_house_card(page: Page):
    """Verify direct drag-and-drop ingestion onto a house card."""
    ingest_calls = []
    _setup_ingest_routes(page, ingest_calls=ingest_calls)

    page.goto("http://localhost:9999/")
    # Wait for house card in grid
    expect(page.locator('.house-card[data-house-id="514"]')).to_be_visible()

    # Trigger direct house drop via window.handleDirectHouseDrop
    page.evaluate("""() => {
        const file = new File(['%PDF-1.4 direct bill'], 'direct_bill_514.pdf', { type: 'application/pdf' });
        return window.handleDirectHouseDrop([file], '514', 'Safra C');
    }""")

    page.wait_for_timeout(500)
    assert len(ingest_calls) == 1
    # Modal should not have been opened
    expect(page.locator("#ingest-station-modal")).to_be_hidden()


def test_direct_drag_drop_category_card(page: Page):
    """Verify direct drag-and-drop ingestion onto a category card in categories view."""
    ingest_calls = []
    _setup_ingest_routes(page, ingest_calls=ingest_calls)

    page.goto("http://localhost:9999/#/area/Safra%20C/house/514")
    page.wait_for_timeout(500)

    # Trigger direct category drop via window.handleDirectCategoryDrop
    page.evaluate("""() => {
        const file = new File(['%PDF-1.4 direct doc'], 'contract_doc.pdf', { type: 'application/pdf' });
        return window.handleDirectCategoryDrop([file], '05 - عقود', '514', 'Safra C');
    }""")

    page.wait_for_timeout(500)
    assert len(ingest_calls) == 1
    expect(page.locator("#ingest-station-modal")).to_be_hidden()
