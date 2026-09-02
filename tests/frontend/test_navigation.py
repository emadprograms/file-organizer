import re
from pathlib import Path
from playwright.sync_api import Page, expect
import pytest

def test_sidebar_renders_and_expands(page: Page):
    html_path = Path(__file__).parent.parent.parent / "src" / "api" / "static" / "index.html"
    
    # Intercept the index.html request
    def handle_index(route):
        route.fulfill(
            status=200,
            content_type="text/html",
            body=html_path.read_text()
        )
    page.route("http://localhost:9999/", handle_index)
    
    def handle_tree(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body="""[
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
                                    "type": "tenant",
                                    "children": []
                                }
                            ]
                        }
                    ]
                }
            ]"""
        )
    page.route("http://localhost:9999/api/tree", handle_tree)
    
    def handle_timeline(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body="""[]"""
        )
    page.route("http://localhost:9999/api/houses/*/timeline", handle_timeline)

    page.goto("http://localhost:9999/")

    # Wait for the tree to render
    expect(page.locator("text=Northside")).to_be_visible()

    # Click the area to expand
    page.click("text=Northside")
    
    # Now house should be visible
    expect(page.locator("#house-list").locator("text=123 - Test House")).to_be_visible()
    
    # Click house to expand
    page.click("text=123 - Test House")
    
    # Now tenant should be visible
    expect(page.locator("text=Ali")).to_be_visible()
    
    # Test deep linking
    page.goto("http://localhost:9999/#/area/area_Northside/house/123 - Test House/tenant/123 - Test House_Ali")
    
    # Tree should automatically expand
    expect(page.locator("#house-list").locator("text=123 - Test House")).to_be_visible()
    expect(page.locator("text=Ali")).to_be_visible()
    
    # The tenant should have selected styling
    tenant_btn = page.locator("li[data-path='/area/area_Northside/house/123 - Test House/tenant/123 - Test House_Ali'] button")
    expect(tenant_btn).to_have_class(re.compile(r".*bg-blue-100.*"))

