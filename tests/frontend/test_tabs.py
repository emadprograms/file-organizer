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
                "children": []
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
        "name": "Ali/Category A",
        "document_count": 2
    },
    {
        "name": "Ali/Category B",
        "document_count": 5
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
    
    # Should load categories
    expect(page.locator("#document-list")).to_contain_text("Category A", timeout=5000)
    expect(page.locator("#document-list")).to_contain_text("2 Documents", timeout=5000)
    assert any("/categories" in u for u in captured)
    
    # Click Timeline tab again
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("Timeline Document", timeout=5000)
