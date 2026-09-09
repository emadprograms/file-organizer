"""Milestone v12.0 End-to-End Verification Test Suite.

Verifies the complete lifecycle of document ingestion across:
- Manual multi-page PDF ingestion via POST /api/ingest
- Batch creation and batches/ storage
- Document creation with is_manual=1 and vault/ storage
- Relational page inheritance in pages table with is_continuation flags
- Real-time search retrievability via /api/search by title and content explanation
- Real-time reflection in /api/areas/{area}/houses/{house}/timeline and /categories
- Preview-AI endpoint heuristics with ZERO database or filesystem mutations
- Comprehensive error handling and validation
"""

from datetime import date
from pathlib import Path
import fitz
import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.db.connection import get_db_connection
from src.db.repository import Repository
from src.db.schema import init_db


def _create_multi_page_pdf(pages_text: list[str]) -> bytes:
    """Create in-memory multi-page PDF bytes with specified text on each page."""
    font_path = None
    for cand in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        if Path(cand).exists():
            font_path = cand
            break

    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page(width=400, height=600)
        if font_path:
            page.insert_font(fontname="testfont", fontfile=font_path)
            page.insert_text((50, 50), text, fontname="testfont")
        else:
            page.insert_text((50, 50), text)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def v12_e2e_env(tmp_path):
    """Isolated environment with mock config, SQLite DB, and areas directory."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir(parents=True, exist_ok=True)
    db_file = tmp_path / "test_organizer_v12.db"

    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn, autocommit=True)

    # Seed baseline area, houses, and tenants
    repo.add_area("Safra C", code="SC")
    repo.add_house("514", area_id="Safra C")
    t1 = repo.add_tenant("514", name="محمد مبارك الشمري", start_date="2020-01-01")

    repo.add_house("515", area_id="Safra C")
    t2 = repo.add_tenant("515", name="علي حسن أحمد", start_date="2021-01-01")

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SC"}
        db_path = str(db_file)

    app.state.config = MockConfig()
    app.state.db_path = str(db_file)
    app.state.repo = repo
    app.state.llm_client = None

    client = TestClient(app)

    return {
        "areas_root": areas_root,
        "db_file": db_file,
        "repo": repo,
        "tenant_id": t1.id,
        "other_tenant_id": t2.id,
        "client": client,
    }


def test_v12_e2e_manual_ingest_lifecycle(v12_e2e_env):
    """VER-03 E2E: Ingest multi-page PDF manually, verify batches, vault, pages inheritance,
    search indexing by title & content explanation, timeline, and categories.
    """
    client = v12_e2e_env["client"]
    repo = v12_e2e_env["repo"]
    areas_root = v12_e2e_env["areas_root"]
    tenant_id = v12_e2e_env["tenant_id"]

    # 1. Prepare a 3-page PDF with realistic Arabic lease and terms text
    pages_content = [
        "صفحة 1: عقد إيجار موثق وشامل لوحدة سكنية",
        "صفحة 2: الشروط والالتزامات التفصيلية للمستأجر",
        "صفحة 3: التوقيعات والشهود وتاريخ السريان",
    ]
    pdf_bytes = _create_multi_page_pdf(pages_content)

    files = {"file": ("lease_contract_full.pdf", pdf_bytes, "application/pdf")}
    data = {
        "mode": "manual",
        "area_id": "Safra C",
        "house_id": "514",
        "tenant_id": tenant_id,
        "category": "05 - عقود",
        "arabic_title": "عقد إيجار موثق وشامل",
        "primary_date": "2023-08-01",
        "notes": "نسخة رسمية مختومة بختم وزارة الإسكان",
    }

    # Execute manual ingestion
    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 200, resp.text
    result = resp.json()

    assert result["status"] == "success"
    assert result["mode"] == "manual"
    assert result["area_id"] == "Safra C"
    assert result["house_id"] == "514"
    assert result["page_count"] == 3
    assert result["documents_created"] == 1

    vault_id = result["vault_id"]
    batch_id = result["batch_id"]
    assert vault_id is not None
    assert batch_id is not None

    # 2. Verify batches row created and file exists in batches/
    batch = repo.get_batch(batch_id)
    assert batch is not None
    assert batch.status == "completed"
    assert batch.page_count == 3
    assert batch.house_id == "514"

    batch_dir = areas_root / "Safra C" / "514" / "batches"
    batch_file = batch_dir / f"batch_{batch_id}_lease_contract_full.pdf"
    assert batch_file.exists(), f"Batch file {batch_file} does not exist"
    assert batch_file.stat().st_size > 0

    with fitz.open(str(batch_file)) as b_doc:
        assert len(b_doc) == 3

    # 3. Verify documents row created with is_manual=1 and file exists in vault/
    doc = repo.get_document(vault_id)
    assert doc is not None
    assert doc.is_manual == 1
    assert doc.arabic_title == "عقد إيجار موثق وشامل"
    assert doc.category == "05 - عقود"
    assert str(doc.primary_date) == "2023-08-01"
    assert doc.notes == "نسخة رسمية مختومة بختم وزارة الإسكان"
    assert doc.tenant_id == tenant_id
    assert doc.page_count == 3

    vault_dir = areas_root / "Safra C" / "514" / "vault"
    vault_file = vault_dir / f"doc_{vault_id}.pdf"
    assert vault_file.exists(), f"Vault file {vault_file} does not exist"
    assert vault_file.stat().st_size > 0

    with fitz.open(str(vault_file)) as v_doc:
        assert len(v_doc) == 3

    # 4. Verify pages rows created, all inheriting parent metadata with is_continuation properly set
    pages = repo.get_pages_by_vault_id(vault_id)
    assert len(pages) == 3

    # Page 1 (Primary page)
    assert pages[0].page_number == 1
    assert pages[0].is_continuation is False
    assert pages[0].content_explanation == "Page 1 of عقد إيجار موثق وشامل"
    assert pages[0].subject == "عقد إيجار موثق وشامل"
    assert pages[0].fine_category == "05 - عقود"
    assert pages[0].fine_category_reason == "Manually verified by user"
    assert pages[0].tenant_id == tenant_id
    assert str(pages[0].resolved_date) == "2023-08-01"
    assert pages[0].vault_id == vault_id

    # Page 2 (Continuation)
    assert pages[1].page_number == 2
    assert pages[1].is_continuation is True
    assert pages[1].content_explanation == "Page 2 of عقد إيجار موثق وشامل"
    assert pages[1].subject is None
    assert pages[1].fine_category == "05 - عقود"
    assert pages[1].tenant_id == tenant_id
    assert str(pages[1].resolved_date) == "2023-08-01"
    assert pages[1].vault_id == vault_id

    # Page 3 (Continuation)
    assert pages[2].page_number == 3
    assert pages[2].is_continuation is True
    assert pages[2].content_explanation == "Page 3 of عقد إيجار موثق وشامل"
    assert pages[2].subject is None
    assert pages[2].fine_category == "05 - عقود"
    assert pages[2].tenant_id == tenant_id
    assert str(pages[2].resolved_date) == "2023-08-01"
    assert pages[2].vault_id == vault_id

    # Verify LLM scratchpad fields remain None for zero-AI purity
    for p in pages:
        assert p.expected_tenant_name is None
        assert p.expected_house_number is None
        assert p.raw_date is None
        assert p.sender is None
        assert p.receiver is None

    # 5. Verify global search /api/search finds the new document by title
    resp_search_title = client.get("/api/search", params={"q": "موثق وشامل"})
    assert resp_search_title.status_code == 200
    results_title = resp_search_title.json()
    matching_title_docs = [
        r for r in results_title if r["type"] == "document" and r.get("vault_id") == vault_id
    ]
    assert len(matching_title_docs) == 1
    assert matching_title_docs[0]["title"] == "عقد إيجار موثق وشامل"
    assert matching_title_docs[0]["is_manual"] == 1
    assert matching_title_docs[0]["house_id"] == "514"

    # Verify global search finds the document by page content_explanation
    resp_search_content = client.get("/api/search", params={"q": "Page 2 of عقد إيجار موثق"})
    assert resp_search_content.status_code == 200
    results_content = resp_search_content.json()
    matching_content_docs = [
        r for r in results_content if r["type"] == "document" and r.get("vault_id") == vault_id
    ]
    assert len(matching_content_docs) == 1

    # 6. Verify /api/areas/{area}/houses/{house}/timeline reflects the new document immediately
    resp_timeline = client.get("/api/areas/Safra C/houses/514/timeline")
    assert resp_timeline.status_code == 200
    timeline_items = resp_timeline.json()
    matching_tl = [item for item in timeline_items if item["vault_id"] == vault_id]
    assert len(matching_tl) == 1
    assert matching_tl[0]["brief_arabic_title"] == "عقد إيجار موثق وشامل"
    assert matching_tl[0]["is_manual"] == 1
    assert "2023-08-01" in matching_tl[0]["dates"]
    assert matching_tl[0]["primary_tenant"] == "محمد مبارك الشمري"
    assert matching_tl[0]["notes"] == "نسخة رسمية مختومة بختم وزارة الإسكان"

    # 7. Verify /api/areas/{area}/houses/{house}/categories reflects the new document immediately
    resp_categories = client.get("/api/areas/Safra C/houses/514/categories")
    assert resp_categories.status_code == 200
    categories = resp_categories.json()
    found_cat = False
    for cat_group in categories:
        for cat_doc in cat_group["documents"]:
            if cat_doc["vault_id"] == vault_id:
                found_cat = True
                assert cat_doc["brief_arabic_title"] == "عقد إيجار موثق وشامل"
                assert cat_doc["is_manual"] == 1
                assert cat_doc["start_page"] == 1
                assert cat_doc["end_page"] == 3
                assert cat_doc["date"] == "2023-08-01"
                assert cat_doc["notes"] == "نسخة رسمية مختومة بختم وزارة الإسكان"
    assert found_cat, f"Document {vault_id} not found in categories response"


def test_v12_e2e_preview_ai_zero_mutations(v12_e2e_env):
    """VER-03 E2E: Test preview endpoint /api/ingest/preview-ai returns suggestions
    and produces ZERO database or filesystem mutations.
    """
    client = v12_e2e_env["client"]
    repo = v12_e2e_env["repo"]
    areas_root = v12_e2e_env["areas_root"]

    # Initial counts and filesystem state
    house_514_batches_dir = areas_root / "Safra C" / "514" / "batches"
    house_514_vault_dir = areas_root / "Safra C" / "514" / "vault"

    batches_before = repo.list_batches_by_house("514")
    docs_before = repo.list_documents_by_house("514")

    # Document text containing Arabic heuristics
    sample_text = (
        "مملكة البحرين - وزارة شؤون الكهرباء والماء\n"
        "فاتورة استهلاك الكهرباء والماء لشهر أكتوبر electricity bill\n"
        "المستفيد / المستأجر: محمد مبارك الشمري\n"
        "منزل رقم 514 مجمع الصافرة House 514\n"
        "بتاريخ: 2023-10-15\n"
    )
    pdf_bytes = _create_multi_page_pdf([sample_text])
    files = {"file": ("preview_bill.pdf", pdf_bytes, "application/pdf")}
    data = {"area_id": "Safra C", "house_id": "514"}

    # Call preview-ai
    resp = client.post("/api/ingest/preview-ai", data=data, files=files)
    assert resp.status_code == 200, resp.text
    preview = resp.json()

    assert preview["status"] == "success"
    assert preview["page_count"] == 1
    assert preview["suggested_category"] == "06-كهرباء وماء"
    assert preview["suggested_date"] == "2023-10-15"
    assert "محمد مبارك الشمري" in preview["suggested_tenant_name"]
    assert preview["suggested_house_id"] == "514"
    assert preview["suggested_area_id"] == "Safra C"
    assert preview["suggested_title"] is not None

    # CRITICAL: Verify ZERO database records created
    batches_after = repo.list_batches_by_house("514")
    docs_after = repo.list_documents_by_house("514")
    assert len(batches_after) == len(batches_before)
    assert len(docs_after) == len(docs_before)

    # CRITICAL: Verify ZERO filesystem artifacts created
    if house_514_batches_dir.exists():
        assert len(list(house_514_batches_dir.glob("*.pdf"))) == 0
    if house_514_vault_dir.exists():
        assert len(list(house_514_vault_dir.glob("*.pdf"))) == 0


def test_v12_e2e_error_handling_and_rejections(v12_e2e_env):
    """VER-03 E2E: Verify rejection of invalid files, modes, and tenant mismatches with zero mutations."""
    client = v12_e2e_env["client"]
    repo = v12_e2e_env["repo"]

    batches_before = repo.list_batches_by_house("514")
    docs_before = repo.list_documents_by_house("514")

    # 1. Non-PDF file extension
    resp = client.post(
        "/api/ingest",
        data={"mode": "manual", "area_id": "Safra C", "house_id": "514"},
        files={"file": ("malicious.exe", b"binary content", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "Invalid file type" in resp.json()["detail"]

    # 2. Corrupt PDF header
    resp = client.post(
        "/api/ingest",
        data={"mode": "manual", "area_id": "Safra C", "house_id": "514"},
        files={"file": ("fake.pdf", b"NOT_A_VALID_PDF_HEADER", "application/pdf")},
    )
    assert resp.status_code == 400
    assert "%PDF" in resp.json()["detail"]

    # 3. Invalid mode
    pdf_bytes = _create_multi_page_pdf(["Sample content"])
    resp = client.post(
        "/api/ingest",
        data={"mode": "unsupported_mode", "area_id": "Safra C", "house_id": "514"},
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 400
    assert "Invalid mode" in resp.json()["detail"]

    # 4. Tenant mismatch (tenant belongs to 515, targeted to 514)
    resp = client.post(
        "/api/ingest",
        data={
            "mode": "manual",
            "area_id": "Safra C",
            "house_id": "514",
            "tenant_id": v12_e2e_env["other_tenant_id"],
        },
        files={"file": ("mismatch.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 400
    assert "belongs to house" in resp.json()["detail"]

    # Verify zero database mutations after all errors
    batches_after = repo.list_batches_by_house("514")
    docs_after = repo.list_documents_by_house("514")
    assert len(batches_after) == len(batches_before)
    assert len(docs_after) == len(docs_before)


def test_v12_e2e_assisted_mode_and_inline_tenant_creation(v12_e2e_env):
    """VER-03 E2E: Ingest with mode='assisted' and inline tenant creation, verifying end-to-end integration."""
    client = v12_e2e_env["client"]
    repo = v12_e2e_env["repo"]

    sample_text = (
        "مملكة البحرين - هيئة الكهرباء والماء\n"
        "فاتورة استهلاك كهرباء وماء electricity water bill\n"
        "المستأجر الجديد: جاسم بن راشد الدوسري\n"
        "بتاريخ: 2024-04-12\n"
    )
    pdf_bytes = _create_multi_page_pdf([sample_text])
    files = {"file": ("assisted_bill.pdf", pdf_bytes, "application/pdf")}
    data = {
        "mode": "assisted",
        "area_id": "Safra C",
        "house_id": "514",
        "tenant_name": "جاسم بن راشد الدوسري",
    }

    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 200, resp.text
    result = resp.json()

    assert result["status"] == "success"
    assert result["mode"] == "assisted"
    vault_id = result["vault_id"]
    assert vault_id is not None

    # Check newly created tenant
    tenants = repo.list_tenants_by_house("514")
    new_tenant = next((t for t in tenants if t.name == "جاسم بن راشد الدوسري"), None)
    assert new_tenant is not None

    # Verify document attributes
    doc = repo.get_document(vault_id)
    assert doc is not None
    assert doc.tenant_id == new_tenant.id
    assert doc.is_manual == 1
    assert str(doc.primary_date) == "2024-04-12"
    assert doc.category == "06-كهرباء وماء"

    # Verify searchable by new tenant name and title
    resp_search = client.get("/api/search", params={"q": "الدوسري"})
    assert resp_search.status_code == 200
    search_results = resp_search.json()
    assert any(r.get("tenant_name") == "جاسم بن راشد الدوسري" for r in search_results)

