"""
Playwright E2E tests for the PDF hover preview feature.

These tests mock the API (no live server needed) and verify:
- Tooltip appears after hovering a timeline card
- Tooltip appears after hovering a category doc link
- Tooltip contains the correct PDF URL in its iframe
- Tooltip title shows the document name
- Tooltip disappears when mouse leaves the element
- No tooltip flicker on fast mouse passes (debounce)
- Tooltip stays open when mouse moves into it
"""
import re
from pathlib import Path
from playwright.sync_api import Page, expect
import pytest

HTML = Path(__file__).parent.parent.parent / "src" / "api" / "static" / "index.html"

TREE_RESPONSE = """[
    {
        "id": "area_Northside",
        "name": "Northside",
        "type": "area",
        "children": [
            {
                "id": "55 - Preview House",
                "name": "55 - Preview House",
                "type": "house",
                "children": [
                    {
                        "id": "55 - Preview House_Ali",
                        "name": "Ali",
                        "type": "tenant",
                        "children": []
                    }
                ]
            }
        ]
    }
]"""

TIMELINE_RESPONSE = """[
    {
        "vault_id": "preview_doc_1",
        "primary_tenant": "Ali",
        "dates": ["2024-06-01"],
        "brief_arabic_title": "عقد إيجار للمعاينة"
    }
]"""

CATEGORIES_RESPONSE = """[
    {
        "tenant": "Ali",
        "name": "01 - Lease Contracts",
        "document_count": 1,
        "documents": [
            {
                "vault_id": "cat_doc_42",
                "filename": "lease.pdf",
                "brief_arabic_title": "وثيقة الإيجار"
            }
        ]
    }
]"""


def _setup_routes(page: Page, pdf_captured: list):
    """Wire all API mocks; capture PDF requests for assertion."""
    page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))

    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text()))

    page.route("http://localhost:9999/api/tree", lambda r: r.fulfill(
        status=200, content_type="application/json", body=TREE_RESPONSE))

    page.route(re.compile(r".*/timeline"), lambda r: r.fulfill(
        status=200, content_type="application/json", body=TIMELINE_RESPONSE))

    page.route(re.compile(r".*/categories"), lambda r: r.fulfill(
        status=200, content_type="application/json", body=CATEGORIES_RESPONSE))

    def handle_pdf(route):
        pdf_captured.append(route.request.url)
        # Return a minimal valid-ish response so the iframe doesn't error
        route.fulfill(status=200, content_type="application/pdf", body=b"%PDF-1.4 placeholder")

    page.route(re.compile(r".*/pdf/.*"), handle_pdf)


# ── Timeline hover ──────────────────────────────────────────────────────────

def test_tooltip_appears_on_timeline_card_hover(page: Page):
    """Hovering a timeline card shows the PDF preview tooltip."""
    pdf_captured = []
    _setup_routes(page, pdf_captured)
    page.goto("http://localhost:9999/")

    # Navigate to the house (loads timeline by default via tab logic)
    page.click("text=Northside")
    page.click("text=55 - Preview House")

    # Switch to Timeline tab
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار للمعاينة", timeout=5000)

    # Hover the timeline card
    card = page.locator("#document-list .p-3.border.rounded-md").first
    card.hover()

    # Tooltip must become visible after debounce (500ms > 350ms delay)
    tooltip = page.locator("#pdf-preview-tooltip")
    expect(tooltip).to_have_class(re.compile(r"visible"), timeout=1000)


def test_tooltip_title_matches_document_on_timeline(page: Page):
    """Preview header shows the hovered document's title."""
    pdf_captured = []
    _setup_routes(page, pdf_captured)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=55 - Preview House")
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار للمعاينة", timeout=5000)

    page.locator("#document-list .p-3.border.rounded-md").first.hover()
    expect(page.locator("#pdf-preview-title")).to_contain_text("عقد إيجار للمعاينة", timeout=1000)


def test_tooltip_iframe_uses_correct_pdf_url_timeline(page: Page):
    """iframe src contains the correct vault_id and area/house path."""
    pdf_captured = []
    _setup_routes(page, pdf_captured)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=55 - Preview House")
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار للمعاينة", timeout=5000)

    page.locator("#document-list .p-3.border.rounded-md").first.hover()
    expect(page.locator("#pdf-preview-tooltip")).to_have_class(re.compile(r"visible"), timeout=1000)

    iframe_src = page.locator("#pdf-preview-iframe").get_attribute("src")
    assert "preview_doc_1" in iframe_src, f"Expected vault_id in iframe src, got: {iframe_src}"
    assert "Northside" in iframe_src, f"Expected area name in iframe src, got: {iframe_src}"
    assert "55" in iframe_src, f"Expected house in iframe src, got: {iframe_src}"


def test_tooltip_disappears_on_mouseleave_timeline(page: Page):
    """Moving the mouse away from a timeline card hides the tooltip."""
    pdf_captured = []
    _setup_routes(page, pdf_captured)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=55 - Preview House")
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار للمعاينة", timeout=5000)

    card = page.locator("#document-list .p-3.border.rounded-md").first
    card.hover()
    expect(page.locator("#pdf-preview-tooltip")).to_have_class(re.compile(r"visible"), timeout=1000)

    # Move away to a neutral element (the main sidebar)
    page.locator("#main-sidebar").hover()
    expect(page.locator("#pdf-preview-tooltip")).not_to_have_class(
        re.compile(r"visible"), timeout=800
    )


# ── Category hover ──────────────────────────────────────────────────────────

def test_tooltip_appears_on_category_doc_link_hover(page: Page):
    """Hovering a category document link shows the PDF preview tooltip."""
    pdf_captured = []
    _setup_routes(page, pdf_captured)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=55 - Preview House")
    page.click("text=Ali")  # click tenant to get tenant-level categories

    # Default tab is categories; expand the category
    expect(page.locator("#document-list")).to_contain_text("01 - Lease Contracts", timeout=5000)
    page.click("text=01 - Lease Contracts")

    # The blue doc link should appear
    expect(page.locator("text=وثيقة الإيجار")).to_be_visible(timeout=3000)

    # Hover it
    page.locator("text=وثيقة الإيجار").hover()
    expect(page.locator("#pdf-preview-tooltip")).to_have_class(re.compile(r"visible"), timeout=1000)


def test_tooltip_iframe_uses_correct_pdf_url_category(page: Page):
    """Category doc link: iframe src contains the correct vault_id."""
    pdf_captured = []
    _setup_routes(page, pdf_captured)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=55 - Preview House")
    page.click("text=Ali")
    expect(page.locator("#document-list")).to_contain_text("01 - Lease Contracts", timeout=5000)
    page.click("text=01 - Lease Contracts")
    expect(page.locator("text=وثيقة الإيجار")).to_be_visible(timeout=3000)

    page.locator("text=وثيقة الإيجار").hover()
    expect(page.locator("#pdf-preview-tooltip")).to_have_class(re.compile(r"visible"), timeout=1000)

    iframe_src = page.locator("#pdf-preview-iframe").get_attribute("src")
    assert "cat_doc_42" in iframe_src, f"Expected cat_doc_42 in iframe src, got: {iframe_src}"


def test_tooltip_disappears_on_mouseleave_category(page: Page):
    """Moving mouse away from a category doc link hides the tooltip."""
    pdf_captured = []
    _setup_routes(page, pdf_captured)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=55 - Preview House")
    page.click("text=Ali")
    expect(page.locator("#document-list")).to_contain_text("01 - Lease Contracts", timeout=5000)
    page.click("text=01 - Lease Contracts")
    expect(page.locator("text=وثيقة الإيجار")).to_be_visible(timeout=3000)

    page.locator("text=وثيقة الإيجار").hover()
    expect(page.locator("#pdf-preview-tooltip")).to_have_class(re.compile(r"visible"), timeout=1000)

    page.locator("#main-sidebar").hover()
    expect(page.locator("#pdf-preview-tooltip")).not_to_have_class(
        re.compile(r"visible"), timeout=800
    )


# ── Debounce / fast-pass ────────────────────────────────────────────────────

def test_tooltip_not_shown_on_fast_mouse_pass(page: Page):
    """Fast mouseenter+mouseleave before debounce fires must not show tooltip."""
    pdf_captured = []
    _setup_routes(page, pdf_captured)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=55 - Preview House")
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار للمعاينة", timeout=5000)

    card = page.locator("#document-list .p-3.border.rounded-md").first

    # Enter and immediately leave before 350ms debounce
    card.hover()
    page.wait_for_timeout(50)
    page.locator("#main-sidebar").hover()
    page.wait_for_timeout(400)   # wait past the would-be show time

    expect(page.locator("#pdf-preview-tooltip")).not_to_have_class(re.compile(r"visible"))


# ── Tooltip self-persistence ────────────────────────────────────────────────

def test_tooltip_stays_visible_when_mouse_enters_it(page: Page):
    """Moving the mouse from the card into the tooltip itself keeps it open."""
    pdf_captured = []
    _setup_routes(page, pdf_captured)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=55 - Preview House")
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار للمعاينة", timeout=5000)

    card = page.locator("#document-list .p-3.border.rounded-md").first
    card.hover()
    expect(page.locator("#pdf-preview-tooltip")).to_have_class(re.compile(r"visible"), timeout=1000)

    # Move mouse into the tooltip
    page.locator("#pdf-preview-tooltip").hover()
    page.wait_for_timeout(300)

    # Tooltip must still be visible
    expect(page.locator("#pdf-preview-tooltip")).to_have_class(re.compile(r"visible"))
