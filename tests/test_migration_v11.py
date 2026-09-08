"""Tests for Phase 93: v11 Legacy Data Migration and Storage Restructuring."""

import json
import sqlite3
from pathlib import Path
import pytest
import yaml

import fitz

from src.db.connection import get_db_connection
from src.db.schema import init_db
from src.db.repository import Repository
from src.migration.v11_migration import (
    extract_house_id,
    normalize_date,
    migrate_house_to_v11,
    migrate_areas,
    verify_migration_integrity,
)


def _create_dummy_pdf(path: Path, num_pages: int = 1) -> None:
    """Helper to create a valid multi-page PDF using PyMuPDF."""
    doc = fitz.open()
    for _ in range(num_pages):
        doc.new_page(width=100, height=100)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))
    doc.close()


@pytest.fixture
def test_db(tmp_path):
    """Fixture providing initialized SQLite database connection and repository."""
    db_file = tmp_path / "test_v11.db"
    conn = get_db_connection(db_file)
    init_db(conn)
    repo = Repository(conn)
    yield db_file, conn, repo
    conn.close()


@pytest.fixture
def legacy_house_fixture(tmp_path):
    """Fixture creating a full mock legacy v5-v10 house directory."""
    area_dir = tmp_path / "Safra C"
    house_dir = area_dir / "514 - محمد مبارك الشمري"
    source_dir = house_dir / ".source_files"
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)

    # 1. Tenants YAML
    tenants_yaml = [
        {"name": "محمد مبارك الشمري", "start_date": "2020-01-01", "end_date": "2022-12-31"},
        {"name": "خالد عبد الله العتيبي", "start_date": "2023-01-01", "end_date": "present"},
    ]
    with open(source_dir / "514_1_tenants.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(tenants_yaml, f, allow_unicode=True)

    # 2. Vault PDFs
    pdf1 = vault_dir / "doc_v001.pdf"
    pdf2 = vault_dir / "doc_v002.pdf"
    _create_dummy_pdf(pdf1, num_pages=2)
    _create_dummy_pdf(pdf2, num_pages=1)

    # 3. Master raw PDF scan
    raw_pdf = source_dir / "514.pdf"
    _create_dummy_pdf(raw_pdf, num_pages=3)

    # 4. State JSON
    state_data = {
        "house_id": "514",
        "cleaned_pages": [
            {
                "original_index": 0,
                "category": "عقود إيجار",
                "content_explanation": "عقد إيجار صفحة 1",
                "expected_tenant_name": "محمد مبارك الشمري",
                "expected_house_number": "514",
                "raw_date": "2020-01-01",
                "is_continuation": False,
                "resolved_date": "2020-01-01",
                "vault_id": "v001",
            },
            {
                "original_index": 1,
                "category": "عقود إيجار",
                "content_explanation": "عقد إيجار صفحة 2",
                "expected_tenant_name": "محمد مبارك الشمري",
                "expected_house_number": "514",
                "raw_date": "2020-01-01",
                "is_continuation": True,
                "resolved_date": "2020-01-01",
                "vault_id": "v001",
            },
            {
                "original_index": 2,
                "category": "كهرباء وماء",
                "content_explanation": "فاتورة كهرباء",
                "expected_tenant_name": "خالد عبد الله العتيبي",
                "expected_house_number": "514",
                "raw_date": "2023-05-15",
                "is_continuation": False,
                "resolved_date": "2023-05-15",
                "vault_id": "v002",
            },
        ],
        "grouped_documents": [
            {
                "vault_id": "v001",
                "start_page": 1,
                "end_page": 2,
                "primary_date": "2020-01-01",
                "brief_arabic_title": "عقد إيجار سكني",
                "category": "عقود إيجار",
                "tenant": "محمد مبارك الشمري",
                "page_count": 2,
            },
            {
                "vault_id": "v002",
                "start_page": 3,
                "end_page": 3,
                "primary_date": "2023-05-15",
                "brief_arabic_title": "فاتورة كهرباء مايو",
                "category": "كهرباء وماء",
                "tenant": "خالد عبد الله العتيبي",
                "page_count": 1,
            },
        ],
    }
    with open(source_dir / "514_state.json", "w", encoding="utf-8") as f:
        json.dump(state_data, f, ensure_ascii=False, indent=2)

    # 5. Legacy folders & .lnk shortcuts
    timeline_dir = house_dir / "[Timeline View]"
    timeline_dir.mkdir(parents=True, exist_ok=True)
    (timeline_dir / "001 - 2020-01-01 - عقد إيجار.lnk").write_text("dummy shortcut")

    contracts_dir = house_dir / "عقود إيجار"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    (contracts_dir / "عقد 2020.lnk").write_text("dummy shortcut")

    return house_dir


def test_extract_house_id():
    """Verify house ID extraction handles various directory naming styles."""
    assert extract_house_id("514 - محمد مبارك الشمري") == "514"
    assert extract_house_id("H01 - Villa South") == "H01"
    assert extract_house_id("514") == "514"
    assert extract_house_id("123 - Test") == "123"


def test_normalize_date():
    """Verify date normalization logic."""
    assert normalize_date("2023-05-15") == "2023-05-15"
    assert normalize_date("2023/05/15") == "2023-05-15"
    assert normalize_date("15-05-2023") == "2023-05-15"
    assert normalize_date("2023-05") == "2023-05-01"
    assert normalize_date("2023") == "2023-01-01"
    assert normalize_date("NONE") is None
    assert normalize_date("nodate") is None
    assert normalize_date("present") is None
    assert normalize_date(None) is None


def test_migrate_house_success(test_db, legacy_house_fixture):
    """Verify full successful migration of a legacy house."""
    db_file, conn, repo = test_db
    house_dir = legacy_house_fixture

    result = migrate_house_to_v11(
        house_dir=house_dir,
        area_id="Safra C",
        area_code="SAF C",
        db_path=db_file,
        conn=conn,
        dry_run=False,
        rename_folder=True,
    )

    assert result["status"] == "success"
    assert result["house_id"] == "514"
    assert result["tenants_migrated"] == 2
    assert result["batches_migrated"] == 1
    assert result["documents_migrated"] == 2
    assert result["pages_migrated"] == 3

    # Database verification
    area = repo.get_area("Safra C")
    assert area is not None
    assert area.code == "SAF C"

    house = repo.get_house("514")
    assert house is not None
    assert house.area_id == "Safra C"

    tenants = repo.list_tenants_by_house("514")
    assert len(tenants) == 2
    tenant_names = [t.name for t in tenants]
    assert "محمد مبارك الشمري" in tenant_names
    assert "خالد عبد الله العتيبي" in tenant_names

    batches = repo.list_batches_by_house("514")
    assert len(batches) == 1
    assert batches[0].page_count == 3
    assert "batch_1_514.pdf" in batches[0].filename

    docs = repo.list_documents_by_house("514")
    assert len(docs) == 2
    doc_ids = {d.vault_id for d in docs}
    assert doc_ids == {"v001", "v002"}

    pages = repo.get_pages_by_batch(batches[0].id)
    assert len(pages) == 3
    assert pages[0].page_number == 1
    assert pages[0].vault_id == "v001"
    assert pages[1].page_number == 2
    assert pages[1].vault_id == "v001"
    assert pages[2].page_number == 3
    assert pages[2].vault_id == "v002"

    # Disk verification
    target_house_dir = house_dir.parent / "514"
    assert target_house_dir.exists()
    assert (target_house_dir / "vault" / "doc_v001.pdf").exists()
    assert (target_house_dir / "vault" / "doc_v002.pdf").exists()
    assert (target_house_dir / "batches" / "batch_1_514.pdf").exists()

    # Legacy clean-up verification
    assert not (target_house_dir / ".source_files").exists()
    assert not (target_house_dir / "[Timeline View]").exists()
    assert not (target_house_dir / "عقود إيجار").exists()
    assert len(list(target_house_dir.glob("*.lnk"))) == 0


def test_migrate_house_idempotency(test_db, legacy_house_fixture):
    """Verify running migration twice produces identical results with no duplicates."""
    db_file, conn, repo = test_db
    house_dir = legacy_house_fixture

    # First run
    res1 = migrate_house_to_v11(
        house_dir=house_dir,
        area_id="Safra C",
        area_code="SAF C",
        db_path=db_file,
        conn=conn,
        dry_run=False,
        rename_folder=True,
    )
    assert res1["status"] == "success"

    migrated_dir = house_dir.parent / "514"
    assert migrated_dir.exists()

    # Second run on migrated directory
    res2 = migrate_house_to_v11(
        house_dir=migrated_dir,
        area_id="Safra C",
        area_code="SAF C",
        db_path=db_file,
        conn=conn,
        dry_run=False,
        rename_folder=True,
    )
    assert res2["status"] in ("success", "already_migrated")

    # Verify no duplicate database rows
    houses = [h for h in repo.list_houses_by_area("Safra C") if h.id == "514"]
    assert len(houses) == 1

    tenants = repo.list_tenants_by_house("514")
    assert len(tenants) == 2

    batches = repo.list_batches_by_house("514")
    assert len(batches) == 1

    docs = repo.list_documents_by_house("514")
    assert len(docs) == 2

    pages = repo.get_pages_by_batch(batches[0].id)
    assert len(pages) == 3


def test_migrate_house_dry_run(test_db, legacy_house_fixture):
    """Verify dry run mode performs zero disk modifications and zero database writes."""
    db_file, conn, repo = test_db
    house_dir = legacy_house_fixture

    result = migrate_house_to_v11(
        house_dir=house_dir,
        area_id="Safra C",
        area_code="SAF C",
        db_path=db_file,
        conn=conn,
        dry_run=True,
        rename_folder=True,
    )
    assert result["dry_run"] is True

    # Disk must be completely untouched
    assert house_dir.exists()
    assert (house_dir / ".source_files").exists()
    assert (house_dir / "[Timeline View]").exists()
    assert (house_dir / "عقود إيجار").exists()
    assert not (house_dir.parent / "514").exists()

    # Database must have 0 rows
    assert repo.get_house("514") is None
    assert len(repo.list_tenants_by_house("514")) == 0
    assert len(repo.list_batches_by_house("514")) == 0
    assert len(repo.list_documents_by_house("514")) == 0


def test_migrate_house_fallback_tenants_and_placeholder_batch(test_db, tmp_path):
    """Verify migration handles missing tenants YAML and missing raw PDF scan."""
    db_file, conn, repo = test_db

    house_dir = tmp_path / "Safra C" / "700 - أحمد السالم"
    source_dir = house_dir / ".source_files"
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)

    # Single vault PDF
    pdf1 = vault_dir / "doc_vx1.pdf"
    _create_dummy_pdf(pdf1, num_pages=1)

    # Report JSON only, no YAML, no state.json
    report_data = [
        {
            "vault_id": "vx1",
            "start_page": 1,
            "end_page": 1,
            "date": "2021-06-01",
            "tenant": "أحمد السالم",
            "folder_path": "فواتير",
            "brief_arabic_title": "فاتورة عامة",
        }
    ]
    with open(source_dir / "700_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False)

    result = migrate_house_to_v11(
        house_dir=house_dir,
        area_id="Safra C",
        db_path=db_file,
        conn=conn,
        dry_run=False,
        rename_folder=True,
    )
    assert result["status"] == "success"
    assert result["house_id"] == "700"

    # Verify tenant inferred
    tenants = repo.list_tenants_by_house("700")
    assert len(tenants) >= 1
    assert tenants[0].name == "أحمد السالم"

    # Verify placeholder batch created
    batches = repo.list_batches_by_house("700")
    assert len(batches) == 1
    assert batches[0].page_count == 1

    # Verify document and page created
    docs = repo.list_documents_by_house("700")
    assert len(docs) == 1
    assert docs[0].vault_id == "vx1"


def test_migrate_house_no_rename_flag(test_db, legacy_house_fixture):
    """Verify rename_folder=False keeps directory name intact while restructuring contents."""
    db_file, conn, repo = test_db
    house_dir = legacy_house_fixture

    result = migrate_house_to_v11(
        house_dir=house_dir,
        area_id="Safra C",
        db_path=db_file,
        conn=conn,
        dry_run=False,
        rename_folder=False,
    )
    assert result["status"] == "success"

    # Directory name preserved
    assert house_dir.exists()
    assert (house_dir / "vault" / "doc_v001.pdf").exists()
    assert (house_dir / "batches" / "batch_1_514.pdf").exists()
    assert not (house_dir / ".source_files").exists()


def test_migrate_areas_batch(test_db, tmp_path):
    """Verify migrate_areas sweeps multiple houses and areas."""
    db_file, conn, repo = test_db
    areas_root = tmp_path / "Areas"

    # Create 2 houses in Safra C
    for hid in ["101", "102"]:
        hdir = areas_root / "Safra C" / f"{hid} - House {hid}"
        vdir = hdir / ".source_files" / "vault"
        vdir.mkdir(parents=True, exist_ok=True)
        pdf = vdir / f"doc_{hid}.pdf"
        _create_dummy_pdf(pdf, num_pages=1)
        with open(hdir / ".source_files" / f"{hid}_report.json", "w", encoding="utf-8") as f:
            json.dump([{"vault_id": hid, "tenant": f"Tenant {hid}", "date": "2022-01-01"}], f)

    results = migrate_areas(
        areas_root_path=areas_root,
        db_path=db_file,
        area_mappings={"Safra C": "SAF C"},
        conn=conn,
        dry_run=False,
    )
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)

    # Verify both houses in DB
    h101 = repo.get_house("101")
    h102 = repo.get_house("102")
    assert h101 is not None
    assert h102 is not None


def test_migration_integrity_verification(test_db, legacy_house_fixture):
    """Verify verification checks match on-disk files with database records."""
    db_file, conn, repo = test_db
    house_dir = legacy_house_fixture

    migrate_house_to_v11(
        house_dir=house_dir,
        area_id="Safra C",
        db_path=db_file,
        conn=conn,
        dry_run=False,
        rename_folder=True,
    )

    migrated_dir = house_dir.parent / "514"
    status = verify_migration_integrity(migrated_dir, "514", repo)
    assert status["is_valid"] is True
    assert len(status["errors"]) == 0

    # Delete one vault file -> verification should fail
    (migrated_dir / "vault" / "doc_v001.pdf").unlink()
    status_corrupt = verify_migration_integrity(migrated_dir, "514", repo)
    assert status_corrupt["is_valid"] is False
    assert any("doc_v001.pdf" in err for err in status_corrupt["errors"])


def test_cli_migrate_v11(tmp_path, monkeypatch):
    """Verify migrate-v11 CLI command execution."""
    from src.main import main

    areas_root = tmp_path / "Areas"
    hdir = areas_root / "Safra C" / "514 - محمد مبارك"
    vdir = hdir / ".source_files" / "vault"
    vdir.mkdir(parents=True, exist_ok=True)
    pdf = vdir / "doc_1.pdf"
    _create_dummy_pdf(pdf, num_pages=1)
    with open(hdir / ".source_files" / "514_report.json", "w", encoding="utf-8") as f:
        json.dump([{"vault_id": "1", "tenant": "محمد مبارك", "date": "2023-01-01"}], f)

    db_path = tmp_path / "cli_test.db"

    # Test dry run CLI
    test_args_dry = [
        "main.py",
        "migrate-v11",
        "--areas-root", str(areas_root),
        "--db-path", str(db_path),
        "--dry-run",
    ]
    monkeypatch.setattr("sys.argv", test_args_dry)
    exit_code = main()
    assert exit_code == 0
    assert hdir.exists()

    # Test real run CLI
    test_args_real = [
        "main.py",
        "migrate-v11",
        "--areas-root", str(areas_root),
        "--db-path", str(db_path),
    ]
    monkeypatch.setattr("sys.argv", test_args_real)
    exit_code = main()
    assert exit_code == 0

    migrated_dir = areas_root / "Safra C" / "514"
    assert migrated_dir.exists()
    assert (migrated_dir / "vault" / "doc_1.pdf").exists()
    assert (migrated_dir / "batches" / "batch_1_514.pdf").exists()

