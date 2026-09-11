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

PROFILE_RESPONSE = """{
    "house_id": "123 - Test House",
    "area_id": "area_Northside",
    "tenants": [
        {
            "id": 1,
            "name": "Ali",
            "start_date": "2024-01-01",
            "end_date": null,
            "is_active": true,
            "duration_str_ar": "سنة واحدة (مستمر)",
            "document_count": 2,
            "category_count": 1
        }
    ],
    "archive": {
        "total_documents": 2,
        "total_pages": 4,
        "batch_count": 1,
        "oldest_date": "2024-01-01",
        "newest_date": "2024-01-01",
        "timespan_years": 1,
        "timespan_str_ar": "2024",
        "categories": [
            {"category": "10 - Category A", "document_count": 2}
        ]
    }
}"""

def _setup_routes(page: Page, captured_urls: list):
    page.on('console', lambda msg: print(f'CONSOLE: {msg.text}'))

    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text()))

    page.route("http://localhost:9999/api/tree", lambda r: r.fulfill(
        status=200, content_type="application/json", body=TREE_RESPONSE))

    def handle_timeline(route):
        captured_urls.append(route.request.url)
        route.fulfill(status=200, content_type="application/json", body=TIMELINE_RESPONSE)
    page.route(re.compile(r".*/api/.*/timeline$"), handle_timeline)

    def handle_categories(route):
        captured_urls.append(route.request.url)
        route.fulfill(status=200, content_type="application/json", body=CATEGORIES_RESPONSE)
    page.route(re.compile(r".*/api/.*/categories$"), handle_categories)

    def handle_profile(route):
        captured_urls.append(route.request.url)
        route.fulfill(status=200, content_type="application/json", body=PROFILE_RESPONSE)
    page.route(re.compile(r".*/profile"), handle_profile)

def test_tabs_switch_and_load_data(page: Page):
    captured = []
    _setup_routes(page, captured)
    
    page.goto("http://localhost:9999/")
    page.click("text=Northside")
    page.click("text=123 - Test House")

    # House level shows Tenancy Register and archive profile by default
    expect(page.locator("#tab-categories-label")).to_contain_text("سجل المستأجرين", timeout=5000)
    expect(page.locator("#document-list")).not_to_contain_text("سجل المستأجرين المتعاقبين")
    expect(page.locator("#document-list")).to_contain_text("Ali", timeout=5000)
    assert any("/profile" in u for u in captured)

    # Click tenant card to drill down into categories
    page.click(".tenant-profile-card >> text=Ali")

    # Should now switch to Folders and load categories
    expect(page.locator("#tab-categories-label")).to_contain_text("Folders", timeout=5000)
    expect(page.locator("#document-list")).to_contain_text("10 - Category A", timeout=5000)
    expect(page.locator(".category-folder-card", has_text="10 - Category A").locator(".doc-count-badge")).to_contain_text("2", timeout=5000)
    expect(page.locator(".category-folder-card", has_text="10 - Category A").locator(".folder-icon-box")).to_be_visible()
    assert any("/categories" in u for u in captured)
    
    # Click to expand the category
    page.click("text=10 - Category A")
    # Should show the document
    expect(page.locator("#document-list")).to_contain_text("Doc 101 Arabic", timeout=5000)
    
    # Click the document to open PDF
    page.click("text=Doc 101 Arabic")
    # Verify PDF viewer opens
    expect(page.locator("#viewer-title")).to_contain_text("Doc 101 Arabic", timeout=5000)
    
    # Click Timeline tab
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("Timeline Document", timeout=5000)
    assert any("/timeline" in u for u in captured)

def test_tabs_tenant_filtering(page: Page):
    captured = []
    _setup_routes(page, captured)
    
    page.goto("http://localhost:9999/")
    page.click("text=Northside")
    page.click("text=123 - Test House")
    
    # Click tenant card in tenancy register
    page.click(".tenant-profile-card >> text=Ali")

    # Should load categories and filter to Ali
    expect(page.locator("#document-list")).to_contain_text("10 - Category A", timeout=5000)
    expect(page.locator("#document-list")).not_to_contain_text("Ali/Category A", timeout=5000)
    
    # Click Timeline tab
    page.click("text=Timeline")
    
    # Timeline should NOT filter by tenant - it should always show house timeline
    expect(page.locator("#document-list")).to_contain_text("Timeline Document", timeout=5000)

def test_tabs_auto_switch_to_categories(page: Page):
    captured = []
    _setup_routes(page, captured)
    
    page.goto("http://localhost:9999/")
    page.click("text=Northside")
    page.click("text=123 - Test House")
    
    # Go to timeline tab
    page.click("text=Timeline")
    expect(page.locator("#document-list")).to_contain_text("Timeline Document", timeout=5000)
    
    # Deep-link to tenant URL
    page.goto("http://localhost:9999/#/area/Northside/house/123 - Test House/tenant/123 - Test House_Ali")
    
    # It should automatically switch back to the Categories tab
    expect(page.locator("#tab-categories-label")).to_contain_text("Folders", timeout=5000)
    expect(page.locator("#document-list")).to_contain_text("10 - Category A", timeout=5000)
