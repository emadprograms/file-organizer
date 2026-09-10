import json
import re
from pathlib import Path
import pytest
from playwright.sync_api import Page, expect

HTML = Path(__file__).parent.parent.parent / "src" / "api" / "static" / "index.html"

TREE_RESPONSE = """[
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
                        "id": "514_Ali",
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

CATEGORIES_RESPONSE = """[
    {
        "tenant": "Ali",
        "name": "06 - كهرباء وماء",
        "document_count": 1,
        "documents": [
            {
                "vault_id": "test_vault_123",
                "filename": "doc_test.pdf",
                "start_page": 1,
                "end_page": 1,
                "date": "2024-01-01",
                "tenant": "Ali",
                "brief_arabic_title": "فاتورة كهرباء",
                "category": "06 - كهرباء وماء"
            }
        ]
    }
]"""

PROFILE_RESPONSE = """{
    "house_id": "514",
    "area_id": "Safra C",
    "tenants": [
        {
            "id": 1,
            "name": "Ali",
            "start_date": "2024-01-01",
            "end_date": null,
            "is_active": true,
            "duration_str_ar": "سنة واحدة (مستمر)",
            "document_count": 1,
            "category_count": 1
        }
    ],
    "archive": {
        "total_documents": 1,
        "total_pages": 1,
        "batch_count": 1,
        "oldest_date": "2024-01-01",
        "newest_date": "2024-01-01",
        "timespan_years": 1,
        "timespan_str_ar": "2024",
        "categories": [
            {"category": "06 - كهرباء وماء", "document_count": 1}
        ]
    }
}"""

def test_delete_doc_dialog_closes(page: Page):
    delete_called = []

    page.on('console', lambda msg: print(f'BROWSER LOG: {msg.text}'))
    page.on('pageerror', lambda err: print(f'BROWSER ERROR: {err}'))

    page.route("http://localhost:9999/", lambda r: r.fulfill(
        status=200, content_type="text/html", body=HTML.read_text()))

    page.route("http://localhost:9999/api/tree", lambda r: r.fulfill(
        status=200, content_type="application/json", body=TREE_RESPONSE))

    page.route(re.compile(r".*/profile$"), lambda r: r.fulfill(
        status=200, content_type="application/json", body=PROFILE_RESPONSE))

    page.route(re.compile(r".*/categories$"), lambda r: r.fulfill(
        status=200, content_type="application/json", body=CATEGORIES_RESPONSE))

    page.route(re.compile(r".*/tenants$"), lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps([{"id": 1, "name": "Ali"}])))

    def handle_delete(route):
        print(f"DELETE URL CALLED: {route.request.url}")
        delete_called.append(route.request.url)
        route.fulfill(status=200, content_type="application/json", body=json.dumps({"status": "success", "message": "deleted"}))

    page.route(re.compile(r".*/documents/.*"), handle_delete)

    page.on("dialog", lambda d: d.accept())

    page.goto("http://localhost:9999/")
    page.click("text=Safra C")
    page.click("text=514")

    # Click tenant to drill down to categories
    page.click(".tenant-profile-card >> text=Ali")
    expect(page.locator("#document-list")).to_contain_text("06 - كهرباء وماء", timeout=5000)

    # Click category card to expand documents
    cat_card = page.locator("[data-category-name='06 - كهرباء وماء']")
    cat_card.click()
    page.wait_for_timeout(300)

    # Hover doc item to reveal 3 dots
    doc_item = page.locator("div[data-vault-id='test_vault_123']")
    doc_item.hover()
    page.wait_for_timeout(200)

    # Click 3-dot button
    menu_btn = page.locator(".doc-menu-btn[data-vault-id='test_vault_123']")
    menu_btn.click()
    page.wait_for_timeout(300)

    # Modal should now be open
    modal = page.locator("#doc-action-modal")
    expect(modal).to_be_visible()

    # Click Delete Document button
    delete_btn = page.locator("#btn-doc-delete")
    delete_btn.click()
    page.wait_for_timeout(1000)

    # VERIFY MODAL CLOSES
    print("Delete called:", delete_called)
    print("Modal class list:", modal.get_attribute("class"))
    expect(modal).to_be_hidden()
