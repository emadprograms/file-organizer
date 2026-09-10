"""
Playwright E2E tests for Ingest Station Multi-File Batch Filing and AI removal.
"""

import json
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
    """Verify switching between Single File and Batch Filing modes."""
    _setup_ingest_routes(page)
    page.goto("http://localhost:9999/")

    page.click("#btn-ingest-trigger")
    expect(page.locator("#ingest-station-modal")).to_be_visible()

    # Single mode default
    expect(page.locator("#ingest-single-container")).to_be_visible()
    expect(page.locator("#ingest-batch-queue-container")).to_be_hidden()
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Ingest Document")

    # Switch to Batch
    page.click("#ingest-mode-batch")
    expect(page.locator("#ingest-single-container")).to_be_hidden()
    expect(page.locator("#ingest-batch-queue-container")).to_be_visible()
    expect(page.locator("#ingest-batch-area-select")).to_be_visible()
    expect(page.locator("#ingest-batch-category-select")).to_be_visible()
    expect(page.locator("#ingest-batch-date-select")).to_be_visible()
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Ingest All (0 Files)")

    # Switch back to Single
    page.click("#ingest-mode-single")
    expect(page.locator("#ingest-single-container")).to_be_visible()
    expect(page.locator("#ingest-batch-queue-container")).to_be_hidden()
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Ingest Document")


def test_batch_filing_queue_population_and_submit(page: Page, tmp_path):
    """Verify uploading multiple files auto-switches to batch, detects houses, and submits sequentially."""
    ingest_calls = []
    _setup_ingest_routes(page, ingest_calls=ingest_calls)

    # Create two temporary test PDF files
    pdf1 = tmp_path / "bill_house_514.pdf"
    pdf1.write_bytes(b"%PDF-1.4 sample bill 514")
    pdf2 = tmp_path / "contract_515.pdf"
    pdf2.write_bytes(b"%PDF-1.4 sample contract 515")

    page.goto("http://localhost:9999/")
    page.click("#btn-ingest-trigger")
    expect(page.locator("#ingest-station-modal")).to_be_visible()

    # Switch to batch mode so multi-file input is enabled
    page.click("#ingest-mode-batch")

    # Upload two files into ingest-file-input
    page.set_input_files("#ingest-file-input", [str(pdf1), str(pdf2)])

    # Modal batch container should be visible
    expect(page.locator("#ingest-batch-queue-container")).to_be_visible()

    # Check that 2 file cards exist in batch queue
    cards = page.locator(".batch-file-card")
    expect(cards).to_have_count(2)

    # Check detected house in first card (514)
    house_select_1 = cards.nth(0).locator(".batch-house-select")
    expect(house_select_1).to_have_value("514")

    # Check detected house in second card (515)
    house_select_2 = cards.nth(1).locator(".batch-house-select")
    expect(house_select_2).to_have_value("515")

    # Select shared category
    page.select_option("#ingest-batch-category-select", "06 - كهرباء وماء")

    # Click Ingest All
    page.click("#btn-ingest-submit")

    # Modal should close on completion
    expect(page.locator("#ingest-station-modal")).to_be_hidden()

    # Verify both requests were posted
    assert len(ingest_calls) == 2


def test_batch_filing_broadcast_document_to_multiple_houses(page: Page, tmp_path):
    """Verify broadcasting a single document to multiple houses via + Add House."""
    ingest_calls = []
    _setup_ingest_routes(page, ingest_calls=ingest_calls)

    notice_pdf = tmp_path / "general_municipality_notice.pdf"
    notice_pdf.write_bytes(b"%PDF-1.4 municipality notice")

    page.goto("http://localhost:9999/")
    page.click("#btn-ingest-trigger")
    expect(page.locator("#ingest-station-modal")).to_be_visible()

    # Switch to batch mode first
    page.click("#ingest-mode-batch")

    # Upload single file in batch mode
    page.set_input_files("#ingest-file-input", [str(notice_pdf)])

    cards = page.locator(".batch-file-card")
    expect(cards).to_have_count(1)

    # Initial target row: house 514
    expect(cards.nth(0).locator(".batch-target-row")).to_have_count(1)
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Ingest All (1 Files)")

    # Click + Add House
    cards.nth(0).locator(".btn-batch-add-house").click()

    # Now 2 target rows for the single file
    expect(cards.nth(0).locator(".batch-target-row")).to_have_count(2)
    expect(page.locator("#ingest-submit-text")).to_have_text("⚡ Ingest All (2 Files)")

    # Ensure second target row is house 515
    second_house_select = cards.nth(0).locator(".batch-target-row").nth(1).locator(".batch-house-select")
    expect(second_house_select).to_have_value("515")

    # Select shared category
    page.select_option("#ingest-batch-category-select", "05 - عقود")

    # Submit
    page.click("#btn-ingest-submit")

    # Modal closes and 2 ingest calls made for this 1 file
    expect(page.locator("#ingest-station-modal")).to_be_hidden()
    assert len(ingest_calls) == 2
