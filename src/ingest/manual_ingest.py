"""Manual Ingestion Pipeline (Zero-AI Direct Ingest).

Provides fast, zero-AI document ingestion directly into SQLite and the
clean storage structure ({area}/{house}/batches/ and {area}/{house}/vault/).
Handles PyMuPDF page counting, batch registration, vault slicing, and
relational page inheritance in the `pages` table.
"""

from datetime import date
import logging
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional, Union
import uuid

import fitz

from src.db.connection import get_db
from src.db.repository import Repository
from src.db.schema import init_db
from src.ingest.v11_ingest import _resolve_fine_category
from src.migration.v11_migration import extract_house_id, normalize_date

logger = logging.getLogger(f"file_organizer.{__name__}")


def extract_pdf_text(pdf_path: Union[str, Path]) -> List[str]:
    """Extract local text from each page of a PDF using PyMuPDF without AI calls."""
    p = Path(pdf_path).resolve()
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"PDF file does not exist: {p}")

    pages_text: List[str] = []
    with fitz.open(str(p)) as doc:
        for page in doc:
            pages_text.append(page.get_text() or "")
    return pages_text


def ingest_document_manual(
    pdf_path: Union[str, Path],
    house_id: str,
    area_id: str,
    tenant_id: int,
    category: str,
    arabic_title: str,
    primary_date: Optional[Union[str, date]] = None,
    db_path: Union[str, Path] = "file_organizer.db",
    areas_root: Union[str, Path] = "areas",
    notes: Optional[str] = None,
    dry_run: bool = False,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
) -> Dict[str, Any]:
    """Ingest a document manually without any LLM calls.

    Performs direct PDF ingestion with PyMuPDF page counting, batch registration,
    vault slicing, and relational page inheritance.

    Args:
        pdf_path: Path to the scanned PDF document.
        house_id: Target house identifier (e.g. '514' or '514 - Tenant Name').
        area_id: Target area identifier (e.g. 'Safra C').
        tenant_id: Database ID of the target tenant.
        category: Selected category/folder name (e.g. '05-عقود' or 'contract').
        arabic_title: Document title in Arabic.
        primary_date: Optional document date (string YYYY-MM-DD or date object).
        db_path: Path to the SQLite database.
        areas_root: Root directory of areas structure.
        notes: Optional user notes for the document.
        dry_run: If True, preview only without modifying database or files.
        start_page: Optional 1-indexed start page for slicing.
        end_page: Optional 1-indexed end page for slicing.

    Returns:
        Dict with status="success", vault_id, batch_id, page_count, house_id, area_id, is_manual=1.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If the PDF has 0 pages or the tenant does not belong to the target house.
    """
    p = Path(pdf_path).resolve()
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"PDF file does not exist: {p}")

    try:
        with fitz.open(str(p)) as doc:
            total_pages = len(doc)
    except fitz.EmptyFileError as e:
        raise ValueError(f"PDF {p.name} contains zero pages or is empty: {e}") from e
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Failed to read PDF {p.name}: {e}") from e

    if total_pages == 0:
        raise ValueError(f"PDF {p.name} contains zero pages.")

    s_page = start_page or 1
    e_page = end_page or total_pages
    if s_page < 1 or e_page > total_pages or s_page > e_page:
        raise ValueError(
            f"Invalid page range {s_page}..{e_page} for PDF '{p.name}' with {total_pages} pages."
        )

    doc_page_count = e_page - s_page + 1
    clean_house_id = extract_house_id(house_id)
    norm_date = normalize_date(primary_date) if primary_date is not None else None

    if dry_run:
        logger.info(
            f"[DRY RUN] Preview manual ingestion for {p.name} ({doc_page_count} pages) "
            f"-> house '{clean_house_id}' in area '{area_id}'"
        )
        return {
            "status": "success",
            "dry_run": True,
            "vault_id": None,
            "batch_id": None,
            "page_count": doc_page_count,
            "house_id": clean_house_id,
            "area_id": area_id,
            "is_manual": 1,
        }

    areas_root_path = Path(areas_root).resolve()
    house_dir = areas_root_path / area_id / clean_house_id
    batches_dir = house_dir / "batches"
    vault_dir = house_dir / "vault"

    batches_dir.mkdir(parents=True, exist_ok=True)
    vault_dir.mkdir(parents=True, exist_ok=True)

    created_files: List[Path] = []
    database_path = Path(db_path).resolve()

    try:
        with get_db(database_path) as conn:
            init_db(conn)
            repo = Repository(conn, autocommit=False)

            # Ensure Area and House exist in DB
            if not repo.get_area(area_id):
                repo.add_area(area_id=area_id)
            if not repo.get_house(clean_house_id):
                repo.add_house(house_id=clean_house_id, area_id=area_id)

            # Verify tenant exists and belongs to this house
            tenant = repo.get_tenant(tenant_id)
            if not tenant:
                raise ValueError(f"Tenant with ID {tenant_id} does not exist.")
            if str(tenant.house_id) != str(clean_house_id):
                raise ValueError(
                    f"Tenant {tenant_id} ('{tenant.name}') belongs to house '{tenant.house_id}', "
                    f"not target house '{clean_house_id}'."
                )

            # Insert batch record (status='completed')
            batch = repo.create_batch(
                house_id=clean_house_id,
                filename=p.name,
                file_path=f"batches/{p.name}",
                page_count=total_pages,
                status="completed",
            )
            batch_id = batch.id
            assert batch_id is not None

            target_batch_filename = f"batch_{batch_id}_{p.name}"
            target_batch_rel = f"batches/{target_batch_filename}"
            target_batch_path = batches_dir / target_batch_filename

            conn.execute(
                "UPDATE batches SET filename = ?, file_path = ? WHERE id = ?",
                (target_batch_filename, target_batch_rel, batch_id),
            )

            # Copy original PDF to {batches_dir}/batch_{batch_id}_{pdf_path.name}
            if p.resolve() != target_batch_path.resolve():
                shutil.copy2(str(p), str(target_batch_path))
                created_files.append(target_batch_path)

            # Generate UUID vault_id
            vault_id = uuid.uuid4().hex
            vault_pdf_filename = f"doc_{vault_id}.pdf"
            vault_pdf_path = vault_dir / vault_pdf_filename

            # Slicing or full copy to vault
            if (start_page is not None or end_page is not None) and (s_page != 1 or e_page != total_pages):
                with fitz.open(str(p)) as src_doc:
                    sub_doc = fitz.open()
                    sub_doc.insert_pdf(src_doc, from_page=s_page - 1, to_page=e_page - 1)
                    sub_doc.save(str(vault_pdf_path))
                    sub_doc.close()
            else:
                shutil.copy2(str(p), str(vault_pdf_path))
            created_files.append(vault_pdf_path)

            # Insert documents record with is_manual=1
            repo.add_document(
                vault_id=vault_id,
                house_id=clean_house_id,
                tenant_id=tenant_id,
                batch_id=batch_id,
                primary_date=norm_date,
                arabic_title=arabic_title,
                category=category,
                page_count=doc_page_count,
                is_manual=1,
                notes=notes,
            )

            # Determine fine_category
            fine_cat, _ = _resolve_fine_category({"category": category})
            if category and ("-" in category and category.split("-", 1)[0].isdigit()):
                fine_category = category
            else:
                fine_category = fine_cat

            # Relational page inheritance for manual documents
            pages_to_add = []
            for page_num in range(1, total_pages + 1):
                in_slice = (s_page <= page_num <= e_page)
                page_vid = vault_id if in_slice else None
                is_cont = bool(page_num > s_page) if in_slice else False

                pages_to_add.append({
                    "batch_id": batch_id,
                    "page_number": page_num,
                    "house_id": clean_house_id,
                    "category": category if in_slice else None,
                    "content_explanation": f"Page {page_num} of {arabic_title}",
                    "expected_tenant_name": None,
                    "expected_house_number": None,
                    "raw_date": None,
                    "sender": None,
                    "receiver": None,
                    "subject": arabic_title if page_num == s_page else None,
                    "is_continuation": is_cont,
                    "tenant_id": tenant_id if in_slice else None,
                    "resolved_date": norm_date if in_slice else None,
                    "fine_category": fine_category if in_slice else None,
                    "fine_category_reason": "Manually verified by user" if in_slice else None,
                    "vault_id": page_vid,
                })

            repo.add_pages_bulk(pages_to_add)

        logger.info(
            f"Successfully manually ingested batch {batch_id} (doc {vault_id}, {doc_page_count} pages) "
            f"for house '{clean_house_id}' ({area_id})."
        )
        return {
            "status": "success",
            "vault_id": vault_id,
            "batch_id": batch_id,
            "page_count": doc_page_count,
            "house_id": clean_house_id,
            "area_id": area_id,
            "is_manual": 1,
        }

    except Exception as e:
        logger.exception(f"Manual ingestion failed for '{p.name}': {e}")
        for f in created_files:
            if f.exists():
                try:
                    f.unlink()
                except OSError:
                    pass
        raise
