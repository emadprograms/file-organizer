"""
Robust Playwright tests for the hierarchical sidebar and timeline loading.

These tests mock the API so they run without a live server.
They are intentionally strict about the URL the frontend calls so regressions
in the area/house path are caught immediately.
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
                "id": "123 - Test House",
                "name": "123 - Test House",
                "type": "house",
                "children": [
                    {
                        "id": "123 - Test House_Ali",
                        "name": "Ali",
                        "type": "tenant",
                        "children": null
                    }
                ]
            },
            {
                "id": "999 - Empty House",
                "name": "999 - Empty House",
                "type": "house",
                "children": []
            }
        ]
    }
]"""

TIMELINE_RESPONSE = """[
    {
        "vault_id": "abc123",
        "primary_tenant": "Ali",
        "dates": ["2024-01-01"],
        "brief_arabic_title": "عقد إيجار"
    }
]"""


def _setup_routes(page: Page, *, timeline_status=200, captured_urls=None):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
    page.on("requestfailed", lambda req: print(f"FAILED: {req.url} - {req.failure}"))
    """Wire up all API mocks. Optionally captures requested URLs into captured_urls list."""
    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text()))

    page.route("http://localhost:9999/api/tree", lambda r: r.fulfill(
        status=200, content_type="application/json", body=TREE_RESPONSE))

    def handle_timeline(route):
        if captured_urls is not None:
            captured_urls.append(route.request.url)
        route.fulfill(
            status=timeline_status,
            content_type="application/json",
            body=TIMELINE_RESPONSE if timeline_status == 200 else '{"detail": "not found"}'
        )
    # Match the new 3-level URL: /api/areas/{area}/houses/{house}/timeline
    page.route(re.compile(r".*/api/areas/.+/houses/.+/timeline"), handle_timeline)

    # Also intercept old URL so the test fails visibly if old URL is used
    def reject_old_timeline(route):
        if captured_urls is not None:
            captured_urls.append("OLD_URL:" + route.request.url)
        route.fulfill(status=404, content_type="application/json",
                      body='{"detail": "old URL still in use"}')
    page.route(re.compile(r".*/api/houses/.+/timeline"), reject_old_timeline)


def test_sidebar_renders_areas_and_houses(page: Page):
    """Tree renders 3 levels: Area → House → Tenant."""
    _setup_routes(page)
    page.goto("http://localhost:9999/")

    # Area visible on load
    expect(page.locator("text=Northside")).to_be_visible()

    # Click area to expand houses
    page.click("text=Northside")
    expect(page.locator("#house-list").locator("text=123 - Test House")).to_be_visible()

    # Click house to expand tenants
    page.click("text=123 - Test House")
    expect(page.locator("#house-list").locator("text=Ali")).to_be_visible()


def test_clicking_tenant_loads_timeline(page: Page):
    """
    Clicking a tenant triggers timeline load via the correct URL:
    /api/areas/{area_name}/houses/{house_id}/timeline
    — NOT the old /api/houses/{house_id}/timeline.
    """
    captured = []
    _setup_routes(page, captured_urls=captured)
    page.goto("http://localhost:9999/")

    # Expand area → house → click tenant
    page.click("text=Northside")
    page.click("text=123 - Test House")
    page.click("text=Ali")

    # Timeline panel must show a document card, not an error
    expect(page.locator("#document-list")).not_to_contain_text("Error loading timeline", timeout=5000)
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار", timeout=5000)
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار", timeout=5000)

    # Assert the URL used was the 3-level one
    assert any("/api/areas/" in u and "/houses/" in u and "/timeline" in u
               for u in captured), \
        f"Timeline was not fetched via /api/areas/{{area}}/houses/{{house}}/timeline. Got: {captured}"
    assert not any(u.startswith("OLD_URL:") for u in captured), \
        f"Old /api/houses/ URL was used: {captured}"


def test_clicking_house_without_tenants_loads_timeline(page: Page):
    """
    Houses with no children (999 - Empty House) must also load the timeline
    when clicked directly — not just silently expand/collapse.
    """
    captured = []
    _setup_routes(page, captured_urls=captured)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=999 - Empty House")

    expect(page.locator("#document-list")).not_to_contain_text("Error loading timeline", timeout=5000)
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار", timeout=5000)
    assert any("/api/areas/" in u and "/houses/" in u and "/timeline" in u
               for u in captured), \
        f"Timeline not fetched for childless house. Got: {captured}"


def test_area_name_not_prefixed_in_api_call(page: Page):
    """
    The area node id in the tree is 'area_Northside' but the API route must
    use the plain area name 'Northside' (without the 'area_' prefix).
    """
    captured = []
    _setup_routes(page, captured_urls=captured)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=123 - Test House")
    page.click("text=Ali")

    page.wait_for_timeout(500)
    for url in captured:
        if "/api/areas/" in url:
            assert "area_Northside" not in url, \
                f"'area_' prefix leaked into API URL: {url}"
            assert "Northside" in url, \
                f"Area name missing from API URL: {url}"


def test_deep_link_expands_tree_and_loads_timeline(page: Page):
    """Navigating to a hash URL auto-expands the tree and loads timeline."""
    captured = []
    _setup_routes(page, captured_urls=captured)

    # Hash uses the tree node id (area_Northside) for matching nodes,
    # but the API call must strip the 'area_' prefix
    page.goto("http://localhost:9999/#/area/area_Northside/house/123 - Test House/tenant/123 - Test House_Ali")

    # Tree must expand automatically
    expect(page.locator("#house-list").locator("text=123 - Test House")).to_be_visible(timeout=5000)
    expect(page.locator("#house-list").locator("text=Ali")).to_be_visible(timeout=5000)

    # Timeline must load without error
    expect(page.locator("#document-list")).not_to_contain_text("Error loading timeline", timeout=5000)
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار", timeout=5000)
    expect(page.locator("#document-list")).to_contain_text("عقد إيجار", timeout=5000)

    # Correct URL used
    assert any("/api/areas/Northside/houses/" in u for u in captured), \
        f"Deep link did not use correct area name in API URL. Got: {captured}"


def test_timeline_error_state_shown_on_404(page: Page):
    """When timeline returns 404 the UI shows the error message, not a blank screen."""
    _setup_routes(page, timeline_status=404)
    page.goto("http://localhost:9999/")

    page.click("text=Northside")
    page.click("text=999 - Empty House")

    expect(page.locator("#document-list")).to_contain_text("Error loading timeline",
                                                       timeout=5000)
