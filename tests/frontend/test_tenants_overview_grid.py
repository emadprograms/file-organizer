"""
Playwright tests for:
1. Tree view removal (flat areas sidebar, no tree elements, no view mode toggle).
2. Default Houses Overview landing with responsive cards.
3. Short Tenants Overview on house cards (current tenant, past tenants, tenure badges, doc counts).
4. Intuitive multi-level navigation:
   - Area Overview -> House Tenancy Register -> Tenant Folders.
   - Return to Tenancy Register via top navbar '#back-to-tenants-btn'.
   - Return to Tenancy Register via banner '#btn-back-to-tenants-list'.
   - Return to Area Overview via '#back-to-grid-btn'.
"""
import re
import json
from pathlib import Path
from playwright.sync_api import Page, expect
import pytest

HTML = Path(__file__).parent.parent.parent / "src" / "api" / "static" / "index.html"

MOCK_TREE = [
    {
        "id": "area_Safra D",
        "name": "Safra D",
        "type": "area",
        "children": [
            {
                "id": "501 - MultiTenantHouse",
                "name": "501 - MultiTenantHouse",
                "type": "house",
                "current_tenant": "Zaid Modern",
                "subtitle": "Since 2022 (2y)",
                "duration_category": "short",
                "total_documents": 7,
                "category_counts": {"عقد الإيجار": 2, "سند قبض": 5},
                "children": [
                    {
                        "id": "501 - MultiTenantHouse_Zaid Modern",
                        "name": "Zaid Modern",
                        "subtitle": "2022 - Present",
                        "duration_category": "short",
                        "type": "tenant"
                    },
                    {
                        "id": "501 - MultiTenantHouse_Tariq Past",
                        "name": "Tariq Past",
                        "subtitle": "2019 - 2022",
                        "duration_category": "short",
                        "type": "tenant"
                    }
                ]
            },
            {
                "id": "502 - SingleTenantHouse",
                "name": "502 - SingleTenantHouse",
                "type": "house",
                "current_tenant": "Khaled Lone",
                "subtitle": "Since 2016 (8y)",
                "duration_category": "medium",
                "total_documents": 4,
                "category_counts": {"عقد الإيجار": 4},
                "children": [
                    {
                        "id": "502 - SingleTenantHouse_Khaled Lone",
                        "name": "Khaled Lone",
                        "subtitle": "2016 - Present",
                        "duration_category": "medium",
                        "type": "tenant"
                    }
                ]
            }
        ]
    }
]

MOCK_PROFILE = {
    "house_id": "501 - MultiTenantHouse",
    "area_id": "Safra D",
    "tenants": [
        {
            "id": 1,
            "name": "Zaid Modern",
            "start_date": "2022-01-01",
            "end_date": None,
            "is_active": True,
            "duration_str_ar": "بدء الإيجار 2022 (مستمر)",
            "document_count": 5,
            "category_count": 2
        },
        {
            "id": 2,
            "name": "Tariq Past",
            "start_date": "2019-01-01",
            "end_date": "2022-01-01",
            "is_active": False,
            "duration_str_ar": "فترة الإيجار: 2019 – 2022",
            "document_count": 2,
            "category_count": 1
        }
    ],
    "archive": {
        "total_documents": 7,
        "total_pages": 14,
        "oldest_document_date": "2019-01-01",
        "newest_document_date": "2024-01-01",
        "timespan_str_ar": "من 2019 إلى 2024",
        "categories": [
            {"category": "05 - عقود", "document_count": 2},
            {"category": "06 - سندات", "document_count": 5}
        ]
    }
}

MOCK_CATEGORIES = [
    {
        "tenant": "Zaid Modern",
        "name": "05 - عقود الإيجار",
        "document_count": 2,
        "documents": [
            {"vault_id": "v1", "filename": "zaid_lease.pdf", "start_page": 1, "end_page": 2, "date": "2022-01-10", "tenant": "Zaid Modern", "brief_arabic_title": "عقد إيجار زيد"}
        ]
    },
    {
        "tenant": "Tariq Past",
        "name": "05 - عقود الإيجار",
        "document_count": 1,
        "documents": [
            {"vault_id": "v2", "filename": "tariq_lease.pdf", "start_page": 1, "end_page": 2, "date": "2019-01-10", "tenant": "Tariq Past", "brief_arabic_title": "عقد إيجار طارق"}
        ]
    }
]

def _setup_tenants_overview_routes(page: Page):
    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text()))
    page.route("http://localhost:9999/api/tree", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps(MOCK_TREE)))
    page.route(re.compile(r".*/profile"), lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps(MOCK_PROFILE)))
    page.route(re.compile(r".*/categories"), lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps(MOCK_CATEGORIES)))
    page.route(re.compile(r".*/timeline"), lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps([
            {"vault_id": "v1", "primary_tenant": "Zaid Modern", "dates": ["2022-01-10"], "brief_arabic_title": "عقد إيجار زيد"}
        ])))


def test_tree_view_completely_removed(page: Page):
    """Verify that tree view controls and DOM hierarchy are completely gone."""
    _setup_tenants_overview_routes(page)
    page.goto("http://localhost:9999/")

    # Mode toggle buttons should not exist
    expect(page.locator("#view-mode-tree")).to_have_count(0)
    expect(page.locator("#view-mode-grid")).to_have_count(0)

    # Sidebar section title is simply "Areas"
    expect(page.locator("#sidebar-section-title")).to_have_text("Areas")

    # Only flat area buttons exist in the sidebar
    expect(page.locator(".area-grid-btn")).to_have_count(1)
    expect(page.locator(".area-grid-btn >> text=Safra D")).to_be_visible()

    # No tree node elements or arrows
    expect(page.locator("span:has-text('▶')")).to_have_count(0)


def test_house_card_tenants_overview_details(page: Page):
    """Verify house card displays meaningful tenants overview instead of category pills."""
    _setup_tenants_overview_routes(page)
    page.goto("http://localhost:9999/")

    # Houses Overview is default on load
    expect(page.locator("#area-grid-panel")).to_be_visible()
    expect(page.locator("#grid-area-title")).to_have_text("Safra D")

    # Multi-tenant house card
    card = page.locator('.house-card[data-house-id="501 - MultiTenantHouse"]')
    expect(card).to_be_visible()

    # Card has Tenants Overview header and count
    expect(card.locator(".tenants-overview-section")).to_be_visible()
    expect(card.locator(".tenants-count")).to_contain_text("2 Tenants")

    # Current tenant is highlighted with green dot and 'Current' badge
    expect(card).to_contain_text("Zaid Modern")
    expect(card).to_contain_text("Current")
    expect(card).to_contain_text("2022 - Present")

    # Past tenant is shown with 'Past' badge and period
    expect(card).to_contain_text("Tariq Past")
    expect(card).to_contain_text("Past")
    expect(card).to_contain_text("2019 - 2022")

    # Total archive doc count is shown
    expect(card.locator(".doc-count")).to_contain_text("7 Docs")

    # Category document pills should NOT be present on overview cards
    expect(card).not_to_contain_text("عقد الإيجار")
    expect(card).not_to_contain_text("سند قبض")


def test_intuitive_back_to_tenants_navigation(page: Page):
    """
    Test full multi-level navigation flow:
    1. Click house card -> Tenancy Register opens.
    2. Click tenant -> Folders open, '#back-to-tenants-btn' and banner appear.
    3. Click '#back-to-tenants-btn' -> returns to Tenancy Register.
    4. Click tenant again -> click banner '#btn-back-to-tenants-list' -> returns to Tenancy Register.
    5. Click '#back-to-grid-btn' -> returns to Houses Overview.
    """
    _setup_tenants_overview_routes(page)
    page.goto("http://localhost:9999/")

    # 1. Click house card to open house register
    page.click('.house-card[data-house-id="501 - MultiTenantHouse"]')

    # House view opens with Tenancy Register
    expect(page.locator("#document-list-panel")).to_be_visible()
    expect(page.locator("#current-house-title")).to_contain_text("501 - MultiTenantHouse")
    expect(page.locator("#tab-categories-label")).to_contain_text("سجل المستأجرين")
    expect(page.locator(".tenant-profile-card")).to_have_count(2)

    # In house view (no tenant selected yet):
    # '#back-to-grid-btn' is visible
    expect(page.locator("#back-to-grid-btn")).to_be_visible()
    expect(page.locator("#back-to-grid-btn")).to_contain_text("← Back to Safra D Houses")
    # '#back-to-tenants-btn' MUST be hidden
    expect(page.locator("#back-to-tenants-btn")).to_be_hidden()

    # 2. Click Zaid Modern tenant card to drill into his folders
    page.click('.tenant-profile-card[data-tenant-name="Zaid Modern"]')

    # Now inside tenant folders:
    expect(page.locator("#tab-categories-label")).to_contain_text("Folders")
    expect(page.locator("#document-list")).to_contain_text("05 - عقود الإيجار")

    # Clean breadcrumb title (house / tenant) without embedded Arabic buttons
    expect(page.locator("#current-house-title")).to_contain_text("501 - MultiTenantHouse")
    expect(page.locator("#current-house-title")).to_contain_text("Zaid Modern")
    expect(page.locator("#btn-back-to-house-register")).to_have_count(0)

    # Dedicated '#back-to-tenants-btn' is now VISIBLE in top navbar
    back_tenants_nav = page.locator("#back-to-tenants-btn")
    expect(back_tenants_nav).to_be_visible()
    expect(back_tenants_nav).to_contain_text("← Back to Tenants")

    # Secondary area back button is also visible
    expect(page.locator("#back-to-grid-btn")).to_be_visible()
    expect(page.locator("#back-to-grid-btn")).to_contain_text("← Safra D Houses")

    # Breadcrumb banner inside category list is also visible
    banner_back_btn = page.locator("#btn-back-to-tenants-list")
    expect(banner_back_btn).to_be_visible()
    expect(banner_back_btn).to_contain_text("← Back to Tenants")

    # 3. Click '#back-to-tenants-btn' in top navbar -> returns to Tenancy Register
    back_tenants_nav.click()

    expect(page.locator("#tab-categories-label")).to_contain_text("سجل المستأجرين")
    expect(page.locator(".tenant-profile-card")).to_have_count(2)
    expect(page.locator("#back-to-tenants-btn")).to_be_hidden()
    expect(page.locator("#back-to-grid-btn")).to_contain_text("← Back to Safra D Houses")

    # 4. Click tenant again, and this time use banner back button
    page.click('.tenant-profile-card[data-tenant-name="Zaid Modern"]')
    expect(page.locator("#tab-categories-label")).to_contain_text("Folders")

    page.click("#btn-back-to-tenants-list")
    expect(page.locator("#tab-categories-label")).to_contain_text("سجل المستأجرين")
    expect(page.locator(".tenant-profile-card")).to_have_count(2)

    # 5. From Tenancy Register, click '#back-to-grid-btn' -> returns to Houses Overview
    page.click("#back-to-grid-btn")
    expect(page.locator("#area-grid-panel")).to_be_visible()
    expect(page.locator("#document-list-panel")).to_be_hidden()
    expect(page.locator(".house-card")).to_have_count(2)
