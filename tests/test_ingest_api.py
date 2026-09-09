"""Tests for Phase 98: FastAPI Ingest Endpoints (POST /api/ingest & POST /api/ingest/preview-ai)."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock
import fitz
import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.db.connection import get_db_connection
from src.db.repository import Repository
from src.db.schema import init_db


def _make_pdf_bytes(pages_text: list[str]) -> bytes:
    """Helper to generate in-memory PDF bytes with text on each page."""
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
def api_env(tmp_path):
    """Isolated environment with mock config, SQLite DB, and areas directory."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir(parents=True, exist_ok=True)
    db_file = tmp_path / "test_organizer.db"

    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn, autocommit=True)

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


def test_post_ingest_manual_mode(api_env):
    """Verify POST /api/ingest with mode='manual' stores document and pages with is_manual=1."""
    client = api_env["client"]
    repo = api_env["repo"]
    areas_root = api_env["areas_root"]

    pdf_bytes = _make_pdf_bytes(["Page 1 of sample lease", "Page 2 terms and signature"])
    files = {"file": ("lease_doc.pdf", pdf_bytes, "application/pdf")}
    data = {
        "mode": "manual",
        "area_id": "Safra C",
        "house_id": "514",
        "tenant_id": api_env["tenant_id"],
        "category": "05-عقود",
        "arabic_title": "عقد إيجار جديد",
        "primary_date": "2023-05-15",
        "notes": "Verified manual entry",
    }

    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 200, resp.text
    res_json = resp.json()

    assert res_json["status"] == "success"
    assert res_json["mode"] == "manual"
    assert res_json["house_id"] == "514"
    assert res_json["area_id"] == "Safra C"
    assert res_json["page_count"] == 2
    assert res_json["documents_created"] == 1
    vault_id = res_json["vault_id"]
    assert vault_id is not None
    batch_id = res_json["batch_id"]
    assert batch_id is not None

    # Check database document
    doc = repo.get_document(vault_id)
    assert doc is not None
    assert doc.arabic_title == "عقد إيجار جديد"
    assert doc.category == "05-عقود"
    assert doc.tenant_id == api_env["tenant_id"]
    assert doc.is_manual == 1
    assert doc.page_count == 2
    assert str(doc.primary_date) == "2023-05-15"
    assert doc.notes == "Verified manual entry"

    # Check pages table
    pages = repo.get_pages_by_vault_id(vault_id)
    assert len(pages) == 2
    assert pages[0].fine_category == "05-عقود"

    # Check disk files
    vault_pdf = areas_root / "Safra C" / "514" / "vault" / f"doc_{vault_id}.pdf"
    assert vault_pdf.exists()
    assert vault_pdf.stat().st_size > 0


def test_post_ingest_manual_inline_tenant_creation(api_env):
    """Verify POST /api/ingest creates a new tenant when tenant_name is given without tenant_id."""
    client = api_env["client"]
    repo = api_env["repo"]

    pdf_bytes = _make_pdf_bytes(["Single page doc for new tenant"])
    files = {"file": ("new_tenant_doc.pdf", pdf_bytes, "application/pdf")}
    data = {
        "mode": "manual",
        "area_id": "Safra C",
        "house_id": "514",
        "tenant_name": "فاطمة عبدالله الزايد",
        "category": "01-بيانات أساسية",
        "primary_date": "2024-02-01",
    }

    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 200, resp.text
    res_json = resp.json()
    vault_id = res_json["vault_id"]

    # Verify tenant was created in house 514
    tenants = repo.list_tenants_by_house("514")
    matching = [t for t in tenants if t.name == "فاطمة عبدالله الزايد"]
    assert len(matching) == 1
    new_tenant = matching[0]

    # Verify document is linked to newly created tenant
    doc = repo.get_document(vault_id)
    assert doc.tenant_id == new_tenant.id


def test_post_ingest_manual_default_tenant_creation(api_env):
    """Verify POST /api/ingest creates 'Default Tenant' when house has no tenants and none provided."""
    client = api_env["client"]
    repo = api_env["repo"]

    # House 700 has no tenants initially
    pdf_bytes = _make_pdf_bytes(["Doc for empty house"])
    files = {"file": ("unassigned.pdf", pdf_bytes, "application/pdf")}
    data = {
        "mode": "manual",
        "area_id": "Safra C",
        "house_id": "700",
    }

    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 200, resp.text
    res_json = resp.json()
    vault_id = res_json["vault_id"]

    doc = repo.get_document(vault_id)
    assert doc is not None
    tenant = repo.get_tenant(doc.tenant_id)
    assert tenant is not None
    assert tenant.name == "Default Tenant"
    assert doc.category == "13-رسائل متنوعة"
    assert doc.arabic_title == "unassigned"


def test_post_ingest_invalid_file_extension(api_env):
    """Verify POST /api/ingest rejects non-PDF file extensions with HTTP 400."""
    client = api_env["client"]

    files = {"file": ("document.txt", b"plain text data", "text/plain")}
    data = {
        "mode": "manual",
        "area_id": "Safra C",
        "house_id": "514",
    }

    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 400
    assert "Invalid file type" in resp.json()["detail"]


def test_post_ingest_invalid_file_signature(api_env):
    """Verify POST /api/ingest rejects files named .pdf but lacking %PDF header with HTTP 400."""
    client = api_env["client"]

    files = {"file": ("corrupt.pdf", b"NOT_A_REAL_PDF_HEADER", "application/pdf")}
    data = {
        "mode": "manual",
        "area_id": "Safra C",
        "house_id": "514",
    }

    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 400
    assert "%PDF" in resp.json()["detail"]


def test_post_ingest_invalid_mode(api_env):
    """Verify POST /api/ingest rejects invalid modes with HTTP 400."""
    client = api_env["client"]

    pdf_bytes = _make_pdf_bytes(["Test page"])
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    data = {
        "mode": "nonexistent_mode",
        "area_id": "Safra C",
        "house_id": "514",
    }

    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 400
    assert "Invalid mode" in resp.json()["detail"]


def test_post_ingest_tenant_mismatch(api_env):
    """Verify POST /api/ingest returns HTTP 400 when tenant does not belong to the target house."""
    client = api_env["client"]

    pdf_bytes = _make_pdf_bytes(["Mismatch test"])
    files = {"file": ("mismatch.pdf", pdf_bytes, "application/pdf")}
    data = {
        "mode": "manual",
        "area_id": "Safra C",
        "house_id": "514",
        "tenant_id": api_env["other_tenant_id"],  # Belongs to house 515!
    }

    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 400
    assert "belongs to house" in resp.json()["detail"]


def test_preview_ai_suggestions_and_no_db_writes(api_env):
    """Verify POST /api/ingest/preview-ai extracts metadata heuristics without modifying database or files."""
    client = api_env["client"]
    repo = api_env["repo"]

    # Initial state
    batches_before = repo.list_batches_by_house("514")
    docs_before = repo.list_documents_by_house("514")

    # Document text with Arabic contract keywords, tenant name, date, and house hint
    sample_text = (
        "مملكة البحرين - وزارة الإسكان\n"
        "عقد إيجار وحدة سكنية contract lease\n"
        "الموضوع: توثيق عقد الإيجار الرسمي\n"
        "المستأجر: سالم حمد الرميحي\n"
        "منزل رقم 514 مجمع الصافرة House 514\n"
        "بتاريخ: 2023-11-20\n"
    )
    pdf_bytes = _make_pdf_bytes([sample_text])
    files = {"file": ("contract_scan.pdf", pdf_bytes, "application/pdf")}
    data = {"area_id": "Safra C", "house_id": "514"}

    resp = client.post("/api/ingest/preview-ai", data=data, files=files)
    assert resp.status_code == 200, resp.text
    preview = resp.json()

    assert preview["status"] == "success"
    assert preview["page_count"] == 1
    assert preview["suggested_category"] == "05-عقود"
    assert preview["suggested_date"] == "2023-11-20"
    assert "سالم حمد الرميحي" in preview["suggested_tenant_name"]
    assert preview["suggested_house_id"] == "514"
    assert preview["suggested_area_id"] == "Safra C"
    assert preview["suggested_title"] is not None

    # CRITICAL: Verify ZERO database rows were created during preview
    batches_after = repo.list_batches_by_house("514")
    docs_after = repo.list_documents_by_house("514")
    assert len(batches_after) == len(batches_before)
    assert len(docs_after) == len(docs_before)


def test_preview_ai_invalid_file(api_env):
    """Verify POST /api/ingest/preview-ai returns HTTP 400 for non-PDF upload."""
    client = api_env["client"]

    files = {"file": ("preview_err.txt", b"plain text", "text/plain")}
    resp = client.post("/api/ingest/preview-ai", files=files)
    assert resp.status_code == 400


def test_post_ingest_assisted_mode(api_env):
    """Verify POST /api/ingest with mode='assisted' auto-populates omitted fields from preview heuristics."""
    client = api_env["client"]
    repo = api_env["repo"]

    sample_text = (
        "هيئة الكهرباء والماء electricity water\n"
        "فاتورة استهلاك الكهرباء والماء لشهر يونيو\n"
        "المستأجر: محمد مبارك الشمري\n"
        "2024-06-10\n"
    )
    pdf_bytes = _make_pdf_bytes([sample_text])
    files = {"file": ("electricity_bill.pdf", pdf_bytes, "application/pdf")}
    # Omit category, arabic_title, and primary_date to test auto-population
    data = {
        "mode": "assisted",
        "area_id": "Safra C",
        "house_id": "514",
    }

    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 200, resp.text
    res_json = resp.json()

    assert res_json["status"] == "success"
    assert res_json["mode"] == "assisted"
    vault_id = res_json["vault_id"]
    assert vault_id is not None

    doc = repo.get_document(vault_id)
    assert doc is not None
    assert doc.category == "06-كهرباء وماء"
    assert str(doc.primary_date) == "2024-06-10"
    assert doc.tenant_id == api_env["tenant_id"]
    assert doc.is_manual == 1


def test_post_ingest_auto_split_mode(api_env):
    """Verify POST /api/ingest with mode='auto_split' invokes batch splitting."""
    client = api_env["client"]

    pdf_bytes = _make_pdf_bytes(["Batch page 1", "Batch page 2"])
    files = {"file": ("batch_scan.pdf", pdf_bytes, "application/pdf")}
    data = {
        "mode": "auto_split",
        "area_id": "Safra C",
        "house_id": "514",
        "dry_run": "true",
    }

    resp = client.post("/api/ingest", data=data, files=files)
    assert resp.status_code == 200, resp.text
    res_json = resp.json()

    assert res_json["status"] == "success"
    assert res_json["mode"] == "auto_split"
    assert res_json["page_count"] == 2
    assert "vault_ids" in res_json
    assert isinstance(res_json["vault_ids"], list)
    assert res_json["documents_created"] >= 1
