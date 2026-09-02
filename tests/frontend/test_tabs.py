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
                "id": "123 - Test House",
                "name": "123 - Test House",
                "type": "house",
                "children": [
                    {
                        "id": "123 - Test House_Ali",
                        "name": "Ali",
                        "subtitle": "2024",
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
        "vault_id": "doc1",
        "primary_tenant": "Ali",
        "dates": ["2024-01-01"],
        "brief_arabic_title": "Timeline Document"
    }
]"""

CATEGORIES_RESPONSE = """[
    {
        "tenant": "Ali",
        "name": "10 - Category A",
        "document_count": 2,
        "documents": [
            {"vault_id": "doc101", "filename": "file1.pdf", "start_page": 1, "end_page": 1, "date": "2024", "tenant": "Ali", "brief_arabic_title": "Doc 101 Arabic"}
        ]
    },
    {
        "tenant": "Ali",
        "name": "11 - Category B",
        "document_count": 5,
        "documents": []
    },
    {
        "tenant": "Bob",
        "name": "12 - Category C",
        "document_count": 1,
        "documents": []
    }
]"""

def _setup_routes(page: Page, captured_urls: list):
    page.on('console', lambda msg: print(f'CONSOLE: {msg.text}'))

    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text()))

    page.route("http://localhost:9999/api/tree", lambda r: r.fulfill(
        status=200, content_type="application/json", body=TREE_RESPONSE))

    def handle_timeline(route):
        captured_urls.append(route.request.url)
        route.fulfill(status=200, content_type="application/json", body=TIMELINE_RESPONSE)
    page.route(re.compile(r".*/timeline"), handle_timeline)

    def handle_categories(route):
        captured_urls.append(route.request.url)
        route.fulfill(status=200, content_type="application/json", body=CATEGORIES_RESPONSE)
    page.route(re.compile(r".*/categories"), handle_categories)

def test_tabs_switch_and_load_data(page: Page):
    captured = []
    _setup_routes(page, captured)
    
    page.goto("http://localhost:9999/")
    page.click("text=Northside")
    page.click("text=123 - Test House")

    # Should load timeline by default
    expect(page.locator("#document-list")).to_contain_text("Timeline Document", timeout=5000)
    assert any("/timeline" in u for u in captured)
    
    # Click Categories tab
    page.click("text=Categories")
    
    # Should load categories with numbering
    expect(page.locator("#document-list")).to_contain_text("10 - Category A", timeout=5000)
    expect(page.locator("#document-list")).to_contain_text("2 Documents", timeout=5000)
    assert any("/categories" in u for u in captured)
    
    # Click to expand the category
    page.click("text=10 - Category A")
    # Should show the document
    expect(page.locator("#document-list")).to_contain_text("Doc 101 Arabic", timeout=5000)
    
    # Click the document to open PDF
    page.click("text=Doc 101 Arabic")
    # Verify PDF viewer opens (viewer title should match document)
    expect(page.locator("#viewer-title")).to_contain_text("Doc 101 Arabic", timeout=5000)
    
    # Click Timeline tab again
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("Timeline Document", timeout=5000)

def test_tabs_tenant_filtering(page: Page):
    captured = []
    _setup_routes(page, captured)
    
    page.goto("http://localhost:9999/")
    page.click("text=Northside")
    page.click("text=123 - Test House")
    
    # Wait for house to expand and click tenant
    page.click("#house-list >> text=Ali")

    # Should load timeline and filter to Ali
    expect(page.locator("#document-list")).to_contain_text("Timeline Document", timeout=5000)
    
    # Click Categories tab
    page.click("text=Categories")
    
    # Should show ONLY Category A and Category B without 'Ali/' prefix, and they should be numbered
    expect(page.locator("#document-list")).to_contain_text("10 - Category A", timeout=5000)
    expect(page.locator("#document-list")).not_to_contain_text("Ali/Category A", timeout=5000)

def test_tabs_auto_switch_to_timeline(page: Page):
    captured = []
    _setup_routes(page, captured)
    
    page.goto("http://localhost:9999/")
    page.click("text=Northside")
    page.click("text=123 - Test House")
    
    # Go to categories tab
    page.click("text=Categories")
    expect(page.locator("#document-list")).to_contain_text("10 - Category A", timeout=5000)
    
    # Click tenant
    page.click("#house-list >> text=Ali")
    
    # It should automatically switch back to the Timeline tab and show Timeline Document
    expect(page.locator("#document-list")).to_contain_text("Timeline Document", timeout=5000)
