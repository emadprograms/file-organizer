"""
Playwright tests for Area Grid Overview and Tenure Color Visualization.
Tests verify:
- Dual-view toggling (Tree View <-> Grid Overview)
- Sidebar area-only rendering in Grid mode
- House card rendering with tenant, tenure, doc counts, and category breakdown
- Tenure color coding: Green (< 5y), Yellow (5-10y), Red (> 10y)
- Drill-down navigation: card click -> categories/timeline -> Back to Grid button
- Direct URL deep linking to grid view
"""
import re
import json
from pathlib import Path
from playwright.sync_api import Page, expect
import pytest

HTML = Path(__file__).parent.parent.parent / "src" / "api" / "static" / "index.html"

MOCK_TREE = [
    {
        "id": "area_Safra C",
        "name": "Safra C",
        "type": "area",
        "children": [
            {
                "id": "101 - GreenHouse",
                "name": "101 - GreenHouse",
                "type": "house",
                "current_tenant": "Ahmad Green",
                "subtitle": "Since 2023 (1y)",
                "duration_category": "short",
                "total_documents": 5,
                "category_counts": {"عقد الإيجار": 2, "سند قبض": 3},
                "children": [
                    {
                        "id": "101 - GreenHouse_Ahmad Green",
                        "name": "Ahmad Green",
                        "subtitle": "2023 - Present",
                        "duration_category": "short",
                        "type": "tenant"
                    }
                ]
            },
            {
                "id": "102 - YellowHouse",
                "name": "102 - YellowHouse",
                "type": "house",
                "current_tenant": "Khaled Yellow",
                "subtitle": "Since 2018 (6y)",
                "duration_category": "medium",
                "total_documents": 8,
                "category_counts": {"عقد الإيجار": 3, "بيانات شخصية": 2, "إشعار": 3},
                "children": [
                    {
                        "id": "102 - YellowHouse_Khaled Yellow",
                        "name": "Khaled Yellow",
                        "subtitle": "2018 - Present",
                        "duration_category": "medium",
                        "type": "tenant"
                    }
                ]
            },
            {
                "id": "103 - RedHouse",
                "name": "103 - RedHouse",
                "type": "house",
                "current_tenant": "Sami Red",
                "subtitle": "Since 2012 (12y)",
                "duration_category": "long",
                "total_documents": 14,
                "category_counts": {"عقد الإيجار": 4, "سند قبض": 10},
                "children": [
                    {
                        "id": "103 - RedHouse_Sami Red",
                        "name": "Sami Red",
                        "subtitle": "2012 - Present",
                        "duration_category": "long",
                        "type": "tenant"
                    }
                ]
            }
        ]
    },
    {
        "id": "area_Safra D",
        "name": "Safra D",
        "type": "area",
        "children": [
            {
                "id": "201 - DeltaHouse",
                "name": "201 - DeltaHouse",
                "type": "house",
                "current_tenant": "Omar Delta",
                "subtitle": "Since 2021 (3y)",
                "duration_category": "short",
                "total_documents": 2,
                "category_counts": {"عقد الإيجار": 2},
                "children": []
            }
        ]
    }
]

def _setup_grid_routes(page: Page):
    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text()))
    page.route("http://localhost:9999/api/tree", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps(MOCK_TREE)))
    page.route(re.compile(r".*/api/areas/.+/houses/.+/categories"), lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps([
            {"tenant": "Ahmad Green", "name": "عقد الإيجار", "document_count": 2, "documents": []},
            {"tenant": "Ahmad Green", "name": "سند قبض", "document_count": 3, "documents": []}
        ])
    ))
    page.route(re.compile(r".*/api/areas/.+/houses/.+/timeline"), lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps([
            {"vault_id": "v1", "primary_tenant": "Ahmad Green", "dates": ["2024-01-01"], "brief_arabic_title": "عقد إيجار"}
        ])
    ))


def test_view_mode_toggle(page: Page):
    """User can toggle between Tree View and Grid Overview modes."""
    _setup_grid_routes(page)
    page.goto("http://localhost:9999/")

    # On load, Tree View is default
    expect(page.locator("#view-mode-tree")).to_be_visible()
    expect(page.locator("#view-mode-grid")).to_be_visible()
    expect(page.locator("#sidebar-section-title")).to_have_text("Areas & Houses")

    # Switch to Grid View
    page.click("#view-mode-grid")
    expect(page.locator("#sidebar-section-title")).to_have_text("Areas")
    # In Grid view, sidebar shows areas with house counts
    expect(page.locator(".area-grid-btn >> text=Safra C")).to_be_visible()
    expect(page.locator(".area-grid-btn >> text=Safra D")).to_be_visible()

    # Switch back to Tree View
    page.click("#view-mode-tree")
    expect(page.locator("#sidebar-section-title")).to_have_text("Areas & Houses")


def test_grid_area_selection_and_house_cards(page: Page):
    """Selecting an area in Grid View displays responsive house cards with metrics."""
    _setup_grid_routes(page)
    page.goto("http://localhost:9999/")

    # Switch to Grid View
    page.click("#view-mode-grid")

    # Click Safra C area
    page.click(".area-grid-btn >> text=Safra C")

    # Grid panel should be visible
    expect(page.locator("#area-grid-panel")).to_be_visible()
    expect(page.locator("#grid-area-title")).to_have_text("Safra C")
    expect(page.locator("#grid-area-stats")).to_have_text("3 Houses")

    # House cards rendered
    cards = page.locator(".house-card")
    expect(cards).to_have_count(3)

    # Check Green House card details
    green_card = page.locator('.house-card[data-house-id="101 - GreenHouse"]')
    expect(green_card).to_contain_text("101 - GreenHouse")
    expect(green_card).to_contain_text("Ahmad Green")
    expect(green_card).to_contain_text("Since 2023 (1y)")
    expect(green_card).to_contain_text("5 Docs")
    expect(green_card).to_contain_text("عقد الإيجار")
    expect(green_card).to_contain_text("سند قبض")


def test_tenure_color_coding(page: Page):
    """Verify tenure color indicators: Green (<5y), Yellow (5-10y), Red (>10y)."""
    _setup_grid_routes(page)
    page.goto("http://localhost:9999/")

    page.click("#view-mode-grid")
    page.click(".area-grid-btn >> text=Safra C")

    # House 1: < 5 years -> Green styling & badge
    card_green = page.locator('.house-card[data-house-id="101 - GreenHouse"]')
    expect(card_green).to_have_class(re.compile(r"border-l-emerald-500"))
    expect(card_green.locator(".tenure-badge")).to_contain_text("< 5 Yrs")

    # House 2: 5-10 years -> Yellow styling & badge
    card_yellow = page.locator('.house-card[data-house-id="102 - YellowHouse"]')
    expect(card_yellow).to_have_class(re.compile(r"border-l-amber-500"))
    expect(card_yellow.locator(".tenure-badge")).to_contain_text("5–10 Yrs")

    # House 3: > 10 years -> Red styling & badge
    card_red = page.locator('.house-card[data-house-id="103 - RedHouse"]')
    expect(card_red).to_have_class(re.compile(r"border-l-rose-500"))
    expect(card_red.locator(".tenure-badge")).to_contain_text("> 10 Yrs")


def test_drill_down_and_back_navigation(page: Page):
    """Clicking a house card opens Categories/Timeline, and Back button returns to grid."""
    _setup_grid_routes(page)
    page.goto("http://localhost:9999/")

    page.click("#view-mode-grid")
    page.click(".area-grid-btn >> text=Safra C")

    # Click on Green House card
    page.click('.house-card[data-house-id="101 - GreenHouse"]')

    # Grid panel hidden, doc list panel open
    expect(page.locator("#area-grid-panel")).to_be_hidden()
    expect(page.locator("#document-list-panel")).to_be_visible()

    # Back to Grid button visible with label
    back_btn = page.locator("#back-to-grid-btn")
    expect(back_btn).to_be_visible()
    expect(back_btn).to_contain_text("← Back to Safra C Grid")

    # Click Back to Grid button
    back_btn.click()

    # Should return to Safra C grid panel
    expect(page.locator("#area-grid-panel")).to_be_visible()
    expect(page.locator("#document-list-panel")).to_be_hidden()
    expect(back_btn).to_be_hidden()


def test_deep_link_grid_area(page: Page):
    """Direct deep-link #/grid/area/Safra%20C opens Grid View on Safra C automatically."""
    _setup_grid_routes(page)
    page.goto("http://localhost:9999/#/grid/area/Safra%20C")

    # Should be in Grid View mode
    expect(page.locator("#area-grid-panel")).to_be_visible()
    expect(page.locator("#grid-area-title")).to_have_text("Safra C")
    expect(page.locator(".house-card")).to_have_count(3)


def test_loading_state_prevents_premature_no_areas_found(page: Page):
    """Switching to Grid View while data is still loading must show Loading indicator, NOT 'No areas found.'"""
    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text()))
    
    # Hold /api/tree request until we assert the loading state
    tree_route = []
    def handle_tree(route):
        tree_route.append(route)
    page.route("http://localhost:9999/api/tree", handle_tree)

    page.goto("http://localhost:9999/")
    # Click Grid View immediately before tree response arrives
    page.click("#view-mode-grid")

    # MUST NOT display "No areas found."
    expect(page.locator("#house-list")).not_to_contain_text("No areas found.")
    expect(page.locator("#house-list")).to_contain_text("Loading...")

    # Now fulfill the suspended request
    assert len(tree_route) > 0
    tree_route[0].fulfill(status=200, content_type="application/json", body=json.dumps(MOCK_TREE))

    # Once loaded, areas appear
    expect(page.locator(".area-grid-btn >> text=Safra C")).to_be_visible()
    expect(page.locator("#house-list")).not_to_contain_text("No areas found.")




def test_empty_state_shows_no_areas_found(page: Page):
    """When /api/tree genuinely returns an empty list, show 'No areas found.'"""
    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text()))
    page.route("http://localhost:9999/api/tree", lambda r: r.fulfill(
        status=200, content_type="application/json", body="[]"))

    page.goto("http://localhost:9999/")
    expect(page.locator("#house-list")).to_contain_text("No areas found.")

    # Switch to Grid View
    page.click("#view-mode-grid")
    expect(page.locator("#house-list")).to_contain_text("No areas found.")


def test_error_state_shows_error_message(page: Page):
    """When /api/tree fails (e.g. 500 or timeout), show error state instead of 'No areas found.'"""
    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text()))
    page.route("http://localhost:9999/api/tree", lambda r: r.abort("failed"))

    page.goto("http://localhost:9999/")
    expect(page.locator("#house-list")).to_contain_text("Error loading data.")
    expect(page.locator("#house-list")).not_to_contain_text("No areas found.")

