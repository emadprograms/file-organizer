"""Tests for Phase 97: Zero-AI Manual Ingest Engine & Relational Page Inheritance."""

from datetime import date
from pathlib import Path
from unittest.mock import patch
import fitz
import pytest

from src.db.connection import get_db, get_db_connection
from src.db.repository import Repository
from src.db.schema import init_db
from src.ingest.manual_ingest import extract_pdf_text, ingest_document_manual


def _create_test_pdf(path: Path, num_pages: int = 1, text_prefix: str = "Test Page") -> Path:
    """Helper to create a valid multi-page PDF using PyMuPDF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=300, height=400)
        page.insert_text((50, 50), f"{text_prefix} {i + 1}")
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def manual_env(tmp_path):
    """Fixture providing an isolated DB and areas directory structure."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    db_path = tmp_path / "file_organizer_test.db"

    # Initialize schema
    conn = get_db_connection(db_path)
    init_db(conn)
    repo = Repository(conn, autocommit=True)

    # Seed an area, house, and tenant
    repo.add_area("Safra C", code="SC")
    repo.add_house("514", area_id="Safra C")
    tenant1 = repo.add_tenant("514", name="محمد مبارك الشمري", start_date="2020-01-01")

    # Seed another house and tenant for mismatch testing
    repo.add_house("515", area_id="Safra C")
    tenant2 = repo.add_tenant("515", name="علي حسن أحمد", start_date="2021-01-01")

    conn.close()

    return {
        "areas_root": areas_root,
        "db_path": db_path,
        "tenant_id": tenant1.id,
        "other_tenant_id": tenant2.id,
        "tmp_path": tmp_path,
    }


def test_single_page_manual_ingest(manual_env):
    """Verify single-page manual ingestion creates batch, document, and page with is_manual=1."""
    areas_root = manual_env["areas_root"]
    db_path = manual_env["db_path"]
    tenant_id = manual_env["tenant_id"]

    pdf_file = manual_env["tmp_path"] / "uploads" / "single_contract.pdf"
    _create_test_pdf(pdf_file, num_pages=1, text_prefix="Single Page Contract")

    res = ingest_document_manual(
        pdf_path=pdf_file,
        house_id="514",
        area_id="Safra C",
        tenant_id=tenant_id,
        category="05-عقود",
        arabic_title="عقد إيجار جديد",
        primary_date="2023-05-10",
        db_path=db_path,
        areas_root=areas_root,
        notes="تم الاستلام باليد",
    )

    assert res["status"] == "success"
    assert res["is_manual"] == 1
    assert res["page_count"] == 1
    assert res["house_id"] == "514"
    assert res["area_id"] == "Safra C"
    vault_id = res["vault_id"]
    batch_id = res["batch_id"]
    assert vault_id is not None
    assert batch_id is not None

    # Verify disk artifacts
    batch_copy = areas_root / "Safra C" / "514" / "batches" / f"batch_{batch_id}_{pdf_file.name}"
    vault_file = areas_root / "Safra C" / "514" / "vault" / f"doc_{vault_id}.pdf"
    assert batch_copy.exists()
    assert vault_file.exists()

    with fitz.open(str(vault_file)) as v_doc:
        assert len(v_doc) == 1

    # Verify database records
    with get_db(db_path) as conn:
        repo = Repository(conn)
        batch = repo.get_batch(batch_id)
        assert batch is not None
        assert batch.status == "completed"
        assert batch.page_count == 1

        doc = repo.get_document(vault_id)
        assert doc is not None
        assert doc.is_manual == 1
        assert doc.arabic_title == "عقد إيجار جديد"
        assert doc.category == "05-عقود"
        assert str(doc.primary_date) == "2023-05-10"
        assert doc.notes == "تم الاستلام باليد"
        assert doc.tenant_id == tenant_id
        assert doc.page_count == 1

        pages = repo.get_pages_by_vault_id(vault_id)
        assert len(pages) == 1
        p1 = pages[0]
        assert p1.page_number == 1
        assert p1.is_continuation is False
        assert p1.content_explanation == "Page 1 of عقد إيجار جديد"
        assert p1.subject == "عقد إيجار جديد"
        assert p1.fine_category_reason == "Manually verified by user"
        assert p1.fine_category == "05-عقود"
        assert p1.category == "05-عقود"
        assert p1.tenant_id == tenant_id
        assert str(p1.resolved_date) == "2023-05-10"
        assert p1.vault_id == vault_id

        # Verify LLM scratchpad fields remain NULL
        assert p1.expected_tenant_name is None
        assert p1.expected_house_number is None
        assert p1.raw_date is None
        assert p1.sender is None
        assert p1.receiver is None


def test_multi_page_manual_ingest_page_inheritance(manual_env):
    """Verify multi-page manual ingestion correctly propagates page inheritance and is_continuation."""
    areas_root = manual_env["areas_root"]
    db_path = manual_env["db_path"]
    tenant_id = manual_env["tenant_id"]

    pdf_file = manual_env["tmp_path"] / "uploads" / "multi_doc.pdf"
    _create_test_pdf(pdf_file, num_pages=3, text_prefix="Multi Page Doc")

    res = ingest_document_manual(
        pdf_path=pdf_file,
        house_id="514 - محمد مبارك الشمري",  # Test unstripped house identifier
        area_id="Safra C",
        tenant_id=tenant_id,
        category="contract",  # Test raw category mapping to 05-عقود
        arabic_title="ملحق عقد تجديد",
        primary_date=date(2024, 1, 15),
        db_path=db_path,
        areas_root=areas_root,
    )

    assert res["status"] == "success"
    assert res["page_count"] == 3
    assert res["house_id"] == "514"
    vault_id = res["vault_id"]

    with get_db(db_path) as conn:
        repo = Repository(conn)
        doc = repo.get_document(vault_id)
        assert doc is not None
        assert doc.is_manual == 1
        assert doc.page_count == 3
        assert str(doc.primary_date) == "2024-01-15"

        pages = repo.get_pages_by_vault_id(vault_id)
        assert len(pages) == 3

        # Page 1
        assert pages[0].page_number == 1
        assert pages[0].is_continuation is False
        assert pages[0].content_explanation == "Page 1 of ملحق عقد تجديد"
        assert pages[0].subject == "ملحق عقد تجديد"
        assert pages[0].fine_category == "05-عقود"
        assert pages[0].fine_category_reason == "Manually verified by user"
        assert pages[0].tenant_id == tenant_id
        assert str(pages[0].resolved_date) == "2024-01-15"
        assert pages[0].vault_id == vault_id

        # Page 2
        assert pages[1].page_number == 2
        assert pages[1].is_continuation is True
        assert pages[1].content_explanation == "Page 2 of ملحق عقد تجديد"
        assert pages[1].subject is None
        assert pages[1].fine_category == "05-عقود"
        assert pages[1].tenant_id == tenant_id
        assert str(pages[1].resolved_date) == "2024-01-15"
        assert pages[1].vault_id == vault_id

        # Page 3
        assert pages[2].page_number == 3
        assert pages[2].is_continuation is True
        assert pages[2].content_explanation == "Page 3 of ملحق عقد تجديد"
        assert pages[2].subject is None
        assert pages[2].fine_category == "05-عقود"
        assert pages[2].tenant_id == tenant_id
        assert str(pages[2].resolved_date) == "2024-01-15"
        assert pages[2].vault_id == vault_id

        # Verify all LLM fields remain None
        for p in pages:
            assert p.expected_tenant_name is None
            assert p.expected_house_number is None
            assert p.raw_date is None
            assert p.sender is None
            assert p.receiver is None


def test_dry_run_mode(manual_env):
    """Verify dry_run=True returns preview metadata without writing to DB or filesystem."""
    areas_root = manual_env["areas_root"]
    db_path = manual_env["db_path"]
    tenant_id = manual_env["tenant_id"]

    pdf_file = manual_env["tmp_path"] / "uploads" / "preview.pdf"
    _create_test_pdf(pdf_file, num_pages=5)

    res = ingest_document_manual(
        pdf_path=pdf_file,
        house_id="514",
        area_id="Safra C",
        tenant_id=tenant_id,
        category="01-بيانات أساسية",
        arabic_title="استمارة معاينة أولية",
        db_path=db_path,
        areas_root=areas_root,
        dry_run=True,
    )

    assert res["status"] == "success"
    assert res["dry_run"] is True
    assert res["vault_id"] is None
    assert res["batch_id"] is None
    assert res["page_count"] == 5
    assert res["house_id"] == "514"
    assert res["is_manual"] == 1

    # Ensure no disk folders created in areas_root
    house_batches = areas_root / "Safra C" / "514" / "batches"
    house_vault = areas_root / "Safra C" / "514" / "vault"
    assert not house_batches.exists()
    assert not house_vault.exists()

    # Ensure no batches, documents, or pages written to DB
    with get_db(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM batches")
        assert cursor.fetchone()[0] == 0
        cursor = conn.execute("SELECT COUNT(*) FROM documents")
        assert cursor.fetchone()[0] == 0
        cursor = conn.execute("SELECT COUNT(*) FROM pages")
        assert cursor.fetchone()[0] == 0


def test_error_missing_pdf(manual_env):
    """Verify FileNotFoundError raised if target PDF does not exist."""
    areas_root = manual_env["areas_root"]
    db_path = manual_env["db_path"]
    tenant_id = manual_env["tenant_id"]

    non_existent = manual_env["tmp_path"] / "uploads" / "does_not_exist.pdf"

    with pytest.raises(FileNotFoundError, match="PDF file does not exist"):
        ingest_document_manual(
            pdf_path=non_existent,
            house_id="514",
            area_id="Safra C",
            tenant_id=tenant_id,
            category="05-عقود",
            arabic_title="عقد",
            db_path=db_path,
            areas_root=areas_root,
        )


def test_error_zero_pages_pdf(manual_env):
    """Verify ValueError raised if PDF has zero pages or is an empty file."""
    areas_root = manual_env["areas_root"]
    db_path = manual_env["db_path"]
    tenant_id = manual_env["tenant_id"]

    empty_file = manual_env["tmp_path"] / "uploads" / "empty.pdf"
    empty_file.parent.mkdir(parents=True, exist_ok=True)
    empty_file.write_bytes(b"")

    with pytest.raises(ValueError, match="zero pages|empty"):
        ingest_document_manual(
            pdf_path=empty_file,
            house_id="514",
            area_id="Safra C",
            tenant_id=tenant_id,
            category="05-عقود",
            arabic_title="عقد",
            db_path=db_path,
            areas_root=areas_root,
        )


def test_error_invalid_tenant(manual_env):
    """Verify ValueError raised if tenant does not exist or belongs to another house."""
    areas_root = manual_env["areas_root"]
    db_path = manual_env["db_path"]
    other_tenant_id = manual_env["other_tenant_id"]

    pdf_file = manual_env["tmp_path"] / "uploads" / "test.pdf"
    _create_test_pdf(pdf_file, num_pages=1)

    # 1. Non-existent tenant ID (9999)
    with pytest.raises(ValueError, match="Tenant with ID 9999 does not exist"):
        ingest_document_manual(
            pdf_path=pdf_file,
            house_id="514",
            area_id="Safra C",
            tenant_id=9999,
            category="05-عقود",
            arabic_title="عقد",
            db_path=db_path,
            areas_root=areas_root,
        )

    # 2. Tenant belonging to house 515 passed to house 514
    with pytest.raises(ValueError, match="belongs to house '515', not target house '514'"):
        ingest_document_manual(
            pdf_path=pdf_file,
            house_id="514",
            area_id="Safra C",
            tenant_id=other_tenant_id,
            category="05-عقود",
            arabic_title="عقد",
            db_path=db_path,
            areas_root=areas_root,
        )


def test_search_retrievability(manual_env):
    """Verify that manually ingested documents and pages are retrievable via search."""
    areas_root = manual_env["areas_root"]
    db_path = manual_env["db_path"]
    tenant_id = manual_env["tenant_id"]

    pdf_file = manual_env["tmp_path"] / "uploads" / "search_test.pdf"
    _create_test_pdf(pdf_file, num_pages=2)

    res = ingest_document_manual(
        pdf_path=pdf_file,
        house_id="514",
        area_id="Safra C",
        tenant_id=tenant_id,
        category="06-كهرباء وماء",
        arabic_title="فاتورة استهلاك مميزة",
        primary_date="2023-11-20",
        db_path=db_path,
        areas_root=areas_root,
        notes="فاتورة كهرباء خاصة لشهر نوفمبر",
    )
    vault_id = res["vault_id"]

    with get_db(db_path) as conn:
        repo = Repository(conn)

        # 1. Search by exact Arabic title query
        results_title = repo.search_documents("فاتورة استهلاك مميزة", house_id="514")
        assert len(results_title) >= 1
        assert any(d.vault_id == vault_id for d in results_title)

        # 2. Search by notes keyword
        results_notes = repo.search_documents("نوفمبر")
        assert len(results_notes) >= 1
        assert any(d.vault_id == vault_id for d in results_notes)

        # 3. Search by partial vault_id
        results_vid = repo.search_documents(vault_id[:8])
        assert len(results_vid) >= 1
        assert results_vid[0].vault_id == vault_id

        # 4. Search documents via category filter
        cat_docs = repo.list_documents_by_category("514", "06-كهرباء وماء")
        assert len(cat_docs) >= 1
        assert any(d.vault_id == vault_id for d in cat_docs)

        # 5. Retrieve pages by vault_id
        pages = repo.get_pages_by_vault_id(vault_id)
        assert len(pages) == 2
        assert pages[0].content_explanation == "Page 1 of فاتورة استهلاك مميزة"
        assert pages[1].content_explanation == "Page 2 of فاتورة استهلاك مميزة"


def test_vault_slicing_mode(manual_env):
    """Verify optional slicing (start_page..end_page) slices PDF into vault."""
    areas_root = manual_env["areas_root"]
    db_path = manual_env["db_path"]
    tenant_id = manual_env["tenant_id"]

    pdf_file = manual_env["tmp_path"] / "uploads" / "four_pages.pdf"
    _create_test_pdf(pdf_file, num_pages=4, text_prefix="Slice Doc")

    res = ingest_document_manual(
        pdf_path=pdf_file,
        house_id="514",
        area_id="Safra C",
        tenant_id=tenant_id,
        category="05-عقود",
        arabic_title="صفحات مقتطعة",
        start_page=2,
        end_page=3,
        db_path=db_path,
        areas_root=areas_root,
    )

    assert res["status"] == "success"
    assert res["page_count"] == 2
    vault_id = res["vault_id"]

    vault_file = areas_root / "Safra C" / "514" / "vault" / f"doc_{vault_id}.pdf"
    assert vault_file.exists()

    with fitz.open(str(vault_file)) as doc:
        assert len(doc) == 2
        # Verify sliced content came from pages 2 and 3
        text_p1 = doc[0].get_text()
        assert "Slice Doc 2" in text_p1


def test_extract_pdf_text(tmp_path):
    """Verify extract_pdf_text extracts text locally without LLM calls."""
    pdf_file = tmp_path / "text_sample.pdf"
    _create_test_pdf(pdf_file, num_pages=2, text_prefix="Local Text Extraction")

    texts = extract_pdf_text(pdf_file)
    assert len(texts) == 2
    assert "Local Text Extraction 1" in texts[0]
    assert "Local Text Extraction 2" in texts[1]


def test_atomic_rollback_on_failure(manual_env):
    """Verify that if an error occurs during ingestion, newly created files on disk are removed."""
    areas_root = manual_env["areas_root"]
    db_path = manual_env["db_path"]
    tenant_id = manual_env["tenant_id"]

    pdf_file = manual_env["tmp_path"] / "uploads" / "fail_doc.pdf"
    _create_test_pdf(pdf_file, num_pages=2)

    # Patch Repository.add_pages_bulk to raise an error
    with patch("src.ingest.manual_ingest.Repository.add_pages_bulk", side_effect=RuntimeError("Simulated DB error")):
        with pytest.raises(RuntimeError, match="Simulated DB error"):
            ingest_document_manual(
                pdf_path=pdf_file,
                house_id="514",
                area_id="Safra C",
                tenant_id=tenant_id,
                category="05-عقود",
                arabic_title="فشل اختباري",
                db_path=db_path,
                areas_root=areas_root,
            )

    # Ensure no leftover files in batches/ or vault/
    batches_dir = areas_root / "Safra C" / "514" / "batches"
    vault_dir = areas_root / "Safra C" / "514" / "vault"
    assert len(list(batches_dir.glob("*.pdf"))) == 0
    assert len(list(vault_dir.glob("*.pdf"))) == 0
