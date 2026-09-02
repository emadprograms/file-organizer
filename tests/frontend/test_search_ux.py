import re
from pathlib import Path
from playwright.sync_api import Page, expect
import pytest

def setup_mock_routes(page: Page):
    html_path = Path(__file__).parent.parent.parent / "src" / "api" / "static" / "index.html"
    
    def handle_index(route):
        route.fulfill(
            status=200,
            content_type="text/html",
            body=html_path.read_text()
        )
    page.route("http://localhost:9999/", handle_index)
    
    def handle_tree(route):
        route.fulfill(status=200, content_type="application/json", body="[]")
    page.route("http://localhost:9999/api/tree", handle_tree)
    
    def handle_search(route):
        q = route.request.url.split("q=")[-1]
        if "test" in q.lower():
            body = """[
                {"id": "1", "title": "Test Result 1", "subtitle": "Tenant in 123", "type": "tenant", "url": "#/area/1/house/123/tenant/test1"},
                {"id": "2", "title": "Test Result 2", "subtitle": "House 456", "type": "house", "url": "#/area/2/house/456"}
            ]"""
        else:
            body = "[]"
        route.fulfill(status=200, content_type="application/json", body=body)
    page.route("http://localhost:9999/api/search*", handle_search)

def test_search_shortcut_focus(page: Page):
    setup_mock_routes(page)
    page.goto("http://localhost:9999/")
    
    search_input = page.locator("#search-input")
    expect(search_input).not_to_be_focused()
    
    # Press Cmd+K (Mac) or Ctrl+K (Windows/Linux). Playwright handles "ControlOrMeta+K"
    page.keyboard.press("ControlOrMeta+K")
    
    expect(search_input).to_be_focused()

def test_zero_click_search_and_navigation(page: Page):
    setup_mock_routes(page)
    page.goto("http://localhost:9999/")
    
    search_input = page.locator("#search-input")
    search_results = page.locator("#search-results")
    
    # Ensure results are hidden initially
    expect(search_results).to_be_hidden()
    
    # Type without pressing enter
    search_input.fill("test")
    
    # Results should show automatically after debounce (wait up to 1 second)
    expect(search_results).to_be_visible()
    
    # Check results are populated
    expect(page.locator("text=Test Result 1")).to_be_visible()
    expect(page.locator("text=Test Result 2")).to_be_visible()
    
    # Click the first result
    page.click("text=Test Result 1")
    
    # Should navigate (hash change) and hide search results
    expect(page).to_have_url(re.compile(r".*#/area/1/house/123/tenant/test1$"))
    expect(search_results).to_be_hidden()
