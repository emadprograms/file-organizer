"""Tests for Phase 94: v11 Ingestion Pipeline Redesign.

Verifies the database-backed ingestion workflow (src/ingest/v11_ingest.py):
- Ingest multi-page scanned PDFs directly into SQLite and clean disk structure (batches/ and vault/).
- Zero index shifting when adding new batches (prepend).
- Zero .lnk shortcuts, zero state.json/report.json writing, zero legacy reconciler.
- Atomic rollback and cleanup on errors.
"""

import os
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import fitz
import pytest

from src.db.connection import get_db_connection
from src.db.repository import Repository
from src.db.schema import init_db
from src.ingest.v11_ingest import ingest_pdf_to_house


def _create_test_pdf(path: Path, num_pages: int = 1) -> Path:
    """Helper to create a multi-page PDF using PyMuPDF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=300, height=400)
        page.insert_text((50, 50), f"Test PDF Page {i + 1}")
    doc.save(str(path))
    doc.close()
    return path


class MockLLMClient:
    """Mock LLM client returning deterministic page extractions and fine categories."""

    def __init__(self, page_data: Optional[List[Dict[str, Any]]] = None):
        self.page_data = page_data or []
        self.call_count = 0

    def classify_page(
        self, page_num: int, total_pages: int, house_id: str
    ) -> Dict[str, Any]:
        self.call_count += 1
        idx = page_num - 1
        if idx < len(self.page_data):
            return dict(self.page_data[idx])
        return {
            "category": "others",
            "content_explanation": f"Generic page {page_num}",
            "expected_tenant_name": None,
            "expected_house_number": house_id,
            "raw_date": "2022-01-01",
            "is_continuation": False,
            "fine_category": "13-رسائل متنوعة",
            "fine_category_reason": "Default fallback",
        }


@pytest.fixture
def ingest_env(tmp_path):
    """Provides isolated areas_root, test db, and paths."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    db_path = tmp_path / "file_organizer_test.db"
    
    # Initialize DB
    conn = get_db_connection(db_path)
    init_db(conn)
    conn.close()

    return {
        "areas_root": areas_root,
        "db_path": db_path,
        "tmp_path": tmp_path,
    }


def test_single_batch_ingest(ingest_env):
    """Test full ingestion of a 3-page PDF: verify batches, pages, documents, and vault PDFs."""
    areas_root = ingest_env["areas_root"]
    db_path = ingest_env["db_path"]
    area_id = "Safra C"
    house_id = "514"

    # 3-page PDF:
    # Page 1: contract, start of doc 1
    # Page 2: contract, continuation of doc 1
    # Page 3: electricity bill, start of doc 2
    mock_pages = [
        {
            "category": "contract",
            "content_explanation": "عقد إيجار صفحة 1",
            "expected_tenant_name": "محمد مبارك الشمري",
            "expected_house_number": "514",
            "raw_date": "2020-01-01",
            "subject": "عقد إيجار",
            "is_continuation": False,
            "fine_category": "05-عقود",
            "fine_category_reason": "عقد إيجار رسمي",
        },
        {
            "category": "contract",
            "content_explanation": "عقد إيجار صفحة 2",
            "expected_tenant_name": "محمد مبارك الشمري",
            "expected_house_number": "514",
            "raw_date": "2020-01-01",
            "subject": "عقد إيجار",
            "is_continuation": True,
            "fine_category": "05-عقود",
            "fine_category_reason": "تكملة عقد إيجار",
        },
        {
            "category": "utility_bills",
            "content_explanation": "فاتورة كهرباء وماء",
            "expected_tenant_name": "محمد مبارك الشمري",
            "expected_house_number": "514",
            "raw_date": "2021-06-15",
            "subject": "فاتورة كهرباء",
            "is_continuation": False,
            "fine_category": "06-كهرباء وماء",
            "fine_category_reason": "فاتورة استهلاك",
        },
    ]
    mock_llm = MockLLMClient(mock_pages)

    input_pdf = _create_test_pdf(ingest_env["tmp_path"] / "incoming" / "scan_514.pdf", num_pages=3)

    summary = ingest_pdf_to_house(
        pdf_path=input_pdf,
        house_id=house_id,
        area_id=area_id,
        db_path=db_path,
        areas_root=areas_root,
        llm_client=mock_llm,
    )

    # 1. Summary assertions
    assert summary["status"] == "success"
    assert summary["batch_id"] == 1
    assert summary["pages_ingested"] == 3
    assert summary["documents_created"] == 2
    assert len(summary["vault_ids"]) == 2

    # 2. Database assertions
    conn = get_db_connection(db_path)
    repo = Repository(conn)

    # Area and House
    area = repo.get_area(area_id)
    assert area is not None
    house = repo.get_house(house_id)
    assert house is not None
    assert house.area_id == area_id

    # Tenant
    tenants = repo.list_tenants_by_house(house_id)
    assert len(tenants) == 1
    assert tenants[0].name == "محمد مبارك الشمري"

    # Batch
    batches = repo.list_batches_by_house(house_id)
    assert len(batches) == 1
    assert batches[0].id == 1
    assert batches[0].page_count == 3
    assert batches[0].status == "completed"
    assert batches[0].filename == "batch_1_scan_514.pdf"

    # Pages
    pages = repo.get_pages_by_batch(1)
    assert len(pages) == 3
    assert [p.page_number for p in pages] == [1, 2, 3]
    assert pages[0].category == "contract"
    assert pages[0].is_continuation is False
    assert pages[1].is_continuation is True
    assert pages[2].category == "utility_bills"
    assert pages[0].tenant_id == tenants[0].id
    assert pages[1].tenant_id == tenants[0].id
    assert pages[2].tenant_id == tenants[0].id
    assert pages[0].resolved_date == "2020-01-01"
    assert pages[2].resolved_date == "2021-06-15"

    # Documents
    docs = repo.list_documents_by_house(house_id)
    assert len(docs) == 2
    # Ordered by primary_date DESC
    assert docs[0].primary_date == "2021-06-15"
    assert docs[0].page_count == 1
    assert docs[1].primary_date == "2020-01-01"
    assert docs[1].page_count == 2

    # Verify vault_id foreign keys in pages
    assert pages[0].vault_id == docs[1].vault_id
    assert pages[1].vault_id == docs[1].vault_id
    assert pages[2].vault_id == docs[0].vault_id

    conn.close()

    # 3. On-disk structure assertions
    house_dir = areas_root / area_id / house_id
    batches_dir = house_dir / "batches"
    vault_dir = house_dir / "vault"

    assert batches_dir.exists()
    assert vault_dir.exists()

    batch_file = batches_dir / "batch_1_scan_514.pdf"
    assert batch_file.exists()
    doc_fitz = fitz.open(str(batch_file))
    assert len(doc_fitz) == 3
    doc_fitz.close()

    doc_file_1 = vault_dir / f"doc_{docs[1].vault_id}.pdf"
    assert doc_file_1.exists()
    doc_fitz1 = fitz.open(str(doc_file_1))
    assert len(doc_fitz1) == 2  # Sliced 2 pages!
    doc_fitz1.close()

    doc_file_2 = vault_dir / f"doc_{docs[0].vault_id}.pdf"
    assert doc_file_2.exists()
    doc_fitz2 = fitz.open(str(doc_file_2))
    assert len(doc_fitz2) == 1  # Sliced 1 page!
    doc_fitz2.close()

    # 4. Zero legacy burdens
    assert len(list(house_dir.rglob("*.lnk"))) == 0
    assert not (house_dir / "state.json").exists()
    assert not (house_dir / "report.json").exists()
    assert not (house_dir / ".source_files").exists()


def test_multi_batch_prepend_preserves_older_records(ingest_env):
    """Test multi-batch / prepend: ingest a second PDF for the same house.
    
    Verifies that old batch, old pages, and old documents are completely untouched (zero index shifting!).
    Verifies dates sort correctly across batches.
    """
    areas_root = ingest_env["areas_root"]
    db_path = ingest_env["db_path"]
    area_id = "Safra C"
    house_id = "514"

    # Batch 1 (3 pages from 2020)
    mock_pages_b1 = [
        {
            "category": "contract",
            "content_explanation": "Old contract page 1",
            "expected_tenant_name": "محمد مبارك الشمري",
            "raw_date": "2020-01-01",
            "is_continuation": False,
            "fine_category": "05-عقود",
        },
        {
            "category": "contract",
            "content_explanation": "Old contract page 2",
            "expected_tenant_name": "محمد مبارك الشمري",
            "raw_date": "2020-01-01",
            "is_continuation": True,
            "fine_category": "05-عقود",
        },
        {
            "category": "utility_bills",
            "content_explanation": "Old bill",
            "expected_tenant_name": "محمد مبارك الشمري",
            "raw_date": "2020-05-01",
            "is_continuation": False,
            "fine_category": "06-كهرباء وماء",
        },
    ]
    pdf1 = _create_test_pdf(ingest_env["tmp_path"] / "scan_b1.pdf", num_pages=3)
    res1 = ingest_pdf_to_house(
        pdf_path=pdf1,
        house_id=house_id,
        area_id=area_id,
        db_path=db_path,
        areas_root=areas_root,
        llm_client=MockLLMClient(mock_pages_b1),
    )
    assert res1["batch_id"] == 1

    # Inspect DB after batch 1
    conn = get_db_connection(db_path)
    repo = Repository(conn)
    b1_pages = repo.get_pages_by_batch(1)
    b1_docs = repo.list_documents_by_house(house_id)
    b1_page_snapshots = [(p.id, p.batch_id, p.page_number, p.vault_id) for p in b1_pages]
    b1_doc_snapshots = [(d.vault_id, d.primary_date, d.page_count) for d in b1_docs]
    conn.close()

    # Batch 2 (2 pages from 2024 - prepend/newer scan)
    mock_pages_b2 = [
        {
            "category": "letters",
            "content_explanation": "New letter page 1",
            "expected_tenant_name": "خالد عبد الله العتيبي",
            "raw_date": "2024-03-01",
            "is_continuation": False,
            "fine_category": "13-رسائل متنوعة",
        },
        {
            "category": "letters",
            "content_explanation": "New letter page 2",
            "expected_tenant_name": "خالد عبد الله العتيبي",
            "raw_date": "2024-03-02",
            "is_continuation": False,
            "fine_category": "13-رسائل متنوعة",
        },
    ]
    pdf2 = _create_test_pdf(ingest_env["tmp_path"] / "scan_b2.pdf", num_pages=2)
    res2 = ingest_pdf_to_house(
        pdf_path=pdf2,
        house_id=house_id,
        area_id=area_id,
        db_path=db_path,
        areas_root=areas_root,
        llm_client=MockLLMClient(mock_pages_b2),
    )
    assert res2["batch_id"] == 2
    assert res2["pages_ingested"] == 2
    assert res2["documents_created"] == 2

    # Verify DB state after batch 2
    conn = get_db_connection(db_path)
    repo = Repository(conn)

    batches = repo.list_batches_by_house(house_id)
    assert len(batches) == 2
    assert batches[0].id == 1
    assert batches[1].id == 2

    # ZERO INDEX SHIFTING: Verify batch 1 pages are 100% UNTOUCHED
    b1_pages_after = repo.get_pages_by_batch(1)
    b1_pages_after_snapshots = [(p.id, p.batch_id, p.page_number, p.vault_id) for p in b1_pages_after]
    assert b1_pages_after_snapshots == b1_page_snapshots

    # Batch 2 pages have page_number 1 and 2 (NOT 4 and 5!)
    b2_pages = repo.get_pages_by_batch(2)
    assert len(b2_pages) == 2
    assert [p.page_number for p in b2_pages] == [1, 2]

    # Verify all documents across house sort chronologically
    all_docs = repo.list_documents_by_house(house_id)
    assert len(all_docs) == 4
    dates = [d.primary_date for d in all_docs]
    assert dates == ["2024-03-02", "2024-03-01", "2020-05-01", "2020-01-01"]

    # Verify both tenants exist
    tenants = repo.list_tenants_by_house(house_id)
    assert len(tenants) == 2
    t_names = {t.name for t in tenants}
    assert "محمد مبارك الشمري" in t_names
    assert "خالد عبد الله العتيبي" in t_names

    conn.close()


def test_dry_run_ingest(ingest_env):
    """Test dry_run=True previews ingestion without writing files or database rows."""
    areas_root = ingest_env["areas_root"]
    db_path = ingest_env["db_path"]
    area_id = "Safra C"
    house_id = "777"

    mock_pages = [
        {
            "category": "contract",
            "content_explanation": "Preview contract",
            "expected_tenant_name": "سالم العجمي",
            "raw_date": "2022-01-01",
            "is_continuation": False,
        }
    ]
    pdf = _create_test_pdf(ingest_env["tmp_path"] / "preview.pdf", num_pages=1)

    summary = ingest_pdf_to_house(
        pdf_path=pdf,
        house_id=house_id,
        area_id=area_id,
        db_path=db_path,
        areas_root=areas_root,
        llm_client=MockLLMClient(mock_pages),
        dry_run=True,
    )

    assert summary["status"] == "success"
    assert summary["dry_run"] is True
    assert summary["pages_ingested"] == 1

    # Verify DB is completely empty
    conn = get_db_connection(db_path)
    repo = Repository(conn)
    assert repo.get_house(house_id) is None
    assert len(repo.list_batches_by_house(house_id)) == 0
    assert len(repo.list_documents_by_house(house_id)) == 0
    conn.close()

    # Verify no physical directories/files were created
    house_dir = areas_root / area_id / house_id
    assert not house_dir.exists()


def test_rollback_on_error(ingest_env):
    """Test atomic rollback: failure midway rolls back DB transaction and cleans up disk files."""
    areas_root = ingest_env["areas_root"]
    db_path = ingest_env["db_path"]
    area_id = "Safra C"
    house_id = "999"

    class FailingMockLLM:
        def classify_page(self, page_num, total_pages, house_id):
            if page_num == 2:
                raise RuntimeError("Simulated OCR failure on page 2")
            return {
                "category": "contract",
                "content_explanation": "Page 1 ok",
                "expected_tenant_name": "Test Tenant",
                "raw_date": "2023-01-01",
                "is_continuation": False,
            }

    pdf = _create_test_pdf(ingest_env["tmp_path"] / "failing.pdf", num_pages=2)

    with pytest.raises(RuntimeError, match="Simulated OCR failure on page 2"):
        ingest_pdf_to_house(
            pdf_path=pdf,
            house_id=house_id,
            area_id=area_id,
            db_path=db_path,
            areas_root=areas_root,
            llm_client=FailingMockLLM(),
        )

    # Verify DB rolled back: 0 batches, 0 pages, 0 documents for house_id 999
    conn = get_db_connection(db_path)
    repo = Repository(conn)
    batches = repo.list_batches_by_house(house_id)
    assert len(batches) == 0
    docs = repo.list_documents_by_house(house_id)
    assert len(docs) == 0
    cursor = conn.execute("SELECT COUNT(*) FROM pages WHERE house_id = ?", (house_id,))
    assert cursor.fetchone()[0] == 0
    conn.close()

    # Verify disk has zero orphaned files in batches or vault
    batches_dir = areas_root / area_id / house_id / "batches"
    vault_dir = areas_root / area_id / house_id / "vault"
    if batches_dir.exists():
        assert len(list(batches_dir.glob("*.pdf"))) == 0
    if vault_dir.exists():
        assert len(list(vault_dir.glob("*.pdf"))) == 0


def test_cli_parser_v11_options():
    """Verify that get_parser parses --v11 and related CLI flags correctly."""
    from src.main import get_parser
    parser = get_parser()

    args = parser.parse_args([
        "ingest", "/path/to/test.pdf",
        "--v11",
        "--house-id", "514",
        "--area-id", "Safra C",
        "--db-path", "/tmp/test.db",
        "--areas-root", "/tmp/areas",
        "--dry-run",
    ])

    assert args.command == "ingest"
    assert args.v11 is True
    assert args.house_id == "514"
    assert args.area_id == "Safra C"
    assert str(args.db_path) == "/tmp/test.db"
    assert str(args.areas_root) == "/tmp/areas"
    assert args.dry_run is True


def test_run_v11_ingest_mode_and_cli(ingest_env, monkeypatch):
    """Verify run_v11_ingest_mode and main() dispatch with --v11 flag."""
    from types import SimpleNamespace
    from src.ingest.v11_ingest import run_v11_ingest_mode
    from src.main import main

    areas_root = ingest_env["areas_root"]
    db_path = ingest_env["db_path"]
    area_id = "Safra C"
    house_id = "303"

    pdf = _create_test_pdf(ingest_env["tmp_path"] / "scan_303.pdf", num_pages=1)
    
    mock_llm = MockLLMClient([{
        "category": "contract",
        "content_explanation": "CLI Test Doc",
        "expected_tenant_name": "سعد الشمري",
        "raw_date": "2023-01-01",
        "is_continuation": False,
    }])

    # Test run_v11_ingest_mode directly
    args = SimpleNamespace(
        input_path=pdf,
        house_id=house_id,
        area_id=area_id,
        db_path=db_path,
        areas_root=areas_root,
        dry_run=False,
        model=None,
    )
    config = SimpleNamespace(
        areas_root_path=str(areas_root),
        area_mappings={house_id: area_id},
    )

    exit_code = run_v11_ingest_mode(args, config, mock_llm)
    assert exit_code == 0

    # Verify DB
    conn = get_db_connection(db_path)
    repo = Repository(conn)
    assert repo.get_house(house_id) is not None
    docs = repo.list_documents_by_house(house_id)
    assert len(docs) == 1
    assert docs[0].arabic_title == "CLI Test Doc"
    conn.close()

    # Now test CLI main() dispatch with --v11 --dry-run
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "ingest",
            str(pdf),
            "--v11",
            "--house-id", "304",
            "--area-id", "Safra C",
            "--db-path", str(db_path),
            "--areas-root", str(areas_root),
            "--dry-run",
        ],
    )
    # Mock config load in main
    monkeypatch.setattr("src.core.config.AppConfig.load", lambda p: config)

    exit_code_main = main()
    assert exit_code_main == 0

