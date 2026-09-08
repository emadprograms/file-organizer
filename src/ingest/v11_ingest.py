"""V11 Database-Backed Ingestion Engine.

Ingests multi-page scanned PDFs directly into the SQLite database and the
clean two-folder disk structure ({area}/{house}/batches/ and {area}/{house}/vault/),
completely replacing legacy index-shifting math, .lnk shortcuts, state.json/report.json,
and the reconciler loop.
"""

from collections import Counter
import logging
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

import fitz

from src.db.connection import get_db
from src.db.repository import Repository
from src.db.schema import init_db
from src.migration.v11_migration import extract_house_id, normalize_date
from src.routing.config import DIRECT_ROUTING_MAP, FOLDER_PREFIXES

logger = logging.getLogger(f"file_organizer.{__name__}")


def _classify_single_page(
    pdf_path: Path,
    page_num: int,
    total_pages: int,
    house_id: str,
    llm_client: Any = None,
    model: str | None = None,
) -> Dict[str, Any]:
    """Extract and classify metadata for a single page using LLM or client."""
    if llm_client is not None:
        if hasattr(llm_client, "classify_page"):
            res = llm_client.classify_page(page_num, total_pages, house_id)
            if isinstance(res, dict):
                return res
        elif hasattr(llm_client, "generate_content"):
            # Open PDF page text as context
            page_text = ""
            try:
                with fitz.open(str(pdf_path)) as doc:
                    if 1 <= page_num <= len(doc):
                        page_text = doc[page_num - 1].get_text()
            except Exception:
                pass

            prompt = (
                f"Categorize page {page_num} of {total_pages} for house {house_id}.\n"
                f"Page text:\n{page_text[:1000]}"
            )
            try:
                res = llm_client.generate_content(contents=[prompt], model=model)
                return {
                    "category": getattr(res, "category", "others"),
                    "content_explanation": getattr(res, "content_explanation", f"Page {page_num}"),
                    "expected_tenant_name": getattr(res, "expected_tenant_name", None),
                    "expected_house_number": getattr(res, "expected_house_number", house_id),
                    "raw_date": getattr(res, "raw_date", getattr(res, "date", None)),
                    "sender": getattr(res, "sender", None),
                    "receiver": getattr(res, "receiver", None),
                    "subject": getattr(res, "subject", None),
                    "is_continuation": bool(getattr(res, "is_continuation", False)),
                    "fine_category": getattr(res, "fine_category", None),
                    "fine_category_reason": getattr(res, "fine_category_reason", None),
                }
            except Exception as e:
                logger.warning(f"LLM generate_content call failed for page {page_num}: {e}")

    # Default fallback when no LLM or unhandled
    return {
        "category": "others",
        "content_explanation": f"Page {page_num} of {pdf_path.name}",
        "expected_tenant_name": None,
        "expected_house_number": house_id,
        "raw_date": None,
        "sender": None,
        "receiver": None,
        "subject": None,
        "is_continuation": False,
        "fine_category": None,
        "fine_category_reason": None,
    }


def _resolve_fine_category(page: Dict[str, Any], llm_client: Any = None, model: str | None = None) -> Tuple[str, Optional[str]]:
    """Determine fine category and reason for a page."""
    if page.get("fine_category"):
        return page["fine_category"], page.get("fine_category_reason")

    cat = (page.get("category") or "").strip().lower()

    # Check direct mapping
    folder_match = DIRECT_ROUTING_MAP.get(cat)
    if folder_match and folder_match in FOLDER_PREFIXES:
        prefix = FOLDER_PREFIXES[folder_match]
        return f"{prefix}-{folder_match}", f"Mapped directly from category '{cat}'"

    # Check if category matches one of the known folders directly
    for folder, prefix in FOLDER_PREFIXES.items():
        if cat == folder.lower() or cat == f"{prefix}-{folder}".lower():
            return f"{prefix}-{folder}", f"Exact match for folder '{folder}'"

    # Fallback to miscellaneous
    return "13-رسائل متنوعة", "Default fallback category"


def _group_pages_into_documents(pages: List[Dict[str, Any]], house_id: str) -> List[Dict[str, Any]]:
    """Group pages into logical document blocks based on continuation and category."""
    if not pages:
        return []

    docs: List[Dict[str, Any]] = []
    current_chunk: List[Dict[str, Any]] = [pages[0]]

    for p in pages[1:]:
        is_cont = bool(p.get("is_continuation", False))
        same_tenant = (p.get("tenant_id") == current_chunk[-1].get("tenant_id"))
        same_cat = (p.get("category") == current_chunk[-1].get("category"))

        if is_cont and same_tenant:
            current_chunk.append(p)
        else:
            docs.append(_build_document_block(current_chunk, len(docs) + 1, house_id))
            current_chunk = [p]

    if current_chunk:
        docs.append(_build_document_block(current_chunk, len(docs) + 1, house_id))

    return docs


def _build_document_block(chunk: List[Dict[str, Any]], doc_num: int, house_id: str) -> Dict[str, Any]:
    """Create a document summary block from a chunk of pages."""
    start_page = chunk[0]["page_number"]
    end_page = chunk[-1]["page_number"]
    page_count = len(chunk)
    tenant_id = chunk[0].get("tenant_id")

    # First non-empty resolved date in chunk
    primary_date = None
    for p in chunk:
        if p.get("resolved_date"):
            primary_date = p["resolved_date"]
            break

    # Title: prefer subject, then content_explanation, then fallback
    title = None
    for p in chunk:
        if p.get("subject"):
            title = p["subject"]
            break
        if p.get("content_explanation"):
            title = p["content_explanation"]
            break
    if not title:
        title = f"Document {doc_num} (Pages {start_page}-{end_page})"

    category = chunk[0].get("fine_category") or chunk[0].get("category") or "others"

    return {
        "start_page": start_page,
        "end_page": end_page,
        "page_count": page_count,
        "tenant_id": tenant_id,
        "primary_date": primary_date,
        "arabic_title": title,
        "category": category,
        "pages": chunk,
    }


def ingest_pdf_to_house(
    pdf_path: Path,
    house_id: str,
    area_id: str,
    db_path: Path,
    areas_root: Path,
    llm_client: Any = None,
    dry_run: bool = False,
    model: str | None = None,
) -> Dict[str, Any]:
    """Ingest a multi-page scanned PDF into the database and clean storage structure.

    Args:
        pdf_path: Path to the scanned PDF.
        house_id: Target house ID (e.g. '514').
        area_id: Target area ID (e.g. 'Safra C').
        db_path: Path to the SQLite database.
        areas_root: Root directory of areas ({areas_root}/{area_id}/{house_id}/).
        llm_client: Optional LLM client or mock for OCR/classification.
        dry_run: If True, preview only without modifying database or files.
        model: Optional model identifier for LLM.

    Returns:
        Summary dict containing batch_id, pages_ingested, documents_created, vault_ids.
    """
    pdf_path = Path(pdf_path).resolve()
    if not pdf_path.exists() or not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")

    areas_root = Path(areas_root).resolve()
    clean_house_id = extract_house_id(house_id)
    house_dir = areas_root / area_id / clean_house_id
    batches_dir = house_dir / "batches"
    vault_dir = house_dir / "vault"

    # Step c: Read page count
    with fitz.open(str(pdf_path)) as doc:
        total_pages = len(doc)
    if total_pages == 0:
        raise ValueError(f"PDF {pdf_path.name} contains zero pages.")

    logger.info(f"Starting v11 ingestion for PDF '{pdf_path.name}' ({total_pages} pages) into house '{clean_house_id}' ({area_id})")

    # Step 1: Run classification/OCR per page
    raw_pages: List[Dict[str, Any]] = []
    if llm_client is not None and hasattr(llm_client, "classify_pages"):
        raw_pages = llm_client.classify_pages(pdf_path, total_pages, house_id=clean_house_id)
    else:
        for page_num in range(1, total_pages + 1):
            p_info = _classify_single_page(
                pdf_path=pdf_path,
                page_num=page_num,
                total_pages=total_pages,
                house_id=clean_house_id,
                llm_client=llm_client,
                model=model,
            )
            p_info["page_number"] = page_num
            raw_pages.append(p_info)

    if dry_run:
        logger.info(f"[DRY RUN] Previewing ingestion of {total_pages} pages for house {clean_house_id}.")
        preview_docs = _group_pages_into_documents(raw_pages, clean_house_id)
        return {
            "status": "success",
            "dry_run": True,
            "batch_id": None,
            "pages_ingested": total_pages,
            "documents_created": len(preview_docs),
            "vault_ids": [uuid.uuid4().hex for _ in preview_docs],
            "house_id": clean_house_id,
            "area_id": area_id,
        }

    # Step a: Ensure directories exist on disk
    batches_dir.mkdir(parents=True, exist_ok=True)
    vault_dir.mkdir(parents=True, exist_ok=True)

    created_files: List[Path] = []

    try:
        with get_db(db_path) as conn:
            init_db(conn)
            repo = Repository(conn, autocommit=False)

            # Ensure Area and House exist in DB
            if not repo.get_area(area_id):
                repo.add_area(area_id=area_id)
            if not repo.get_house(clean_house_id):
                repo.add_house(house_id=clean_house_id, area_id=area_id)

            # Step b: Insert batch record (status='processing')
            batch = repo.create_batch(
                house_id=clean_house_id,
                filename=pdf_path.name,
                file_path=f"batches/{pdf_path.name}",
                page_count=total_pages,
                status="processing",
            )
            batch_id = batch.id
            assert batch_id is not None

            target_batch_filename = f"batch_{batch_id}_{pdf_path.name}"
            target_batch_rel = f"batches/{target_batch_filename}"
            target_batch_path = batches_dir / target_batch_filename

            conn.execute(
                "UPDATE batches SET filename = ?, file_path = ? WHERE id = ?",
                (target_batch_filename, target_batch_rel, batch_id),
            )

            # Copy uploaded PDF into batches/batch_{id}_{name}
            if pdf_path.resolve() != target_batch_path.resolve():
                shutil.copy2(str(pdf_path), str(target_batch_path))
                created_files.append(target_batch_path)

            # Step e: Cleaning (tenant matching & date resolution)
            existing_tenants = repo.list_tenants_by_house(clean_house_id)
            tenant_map: Dict[str, int] = {t.name.strip().lower(): t.id for t in existing_tenants if t.id}

            # Find primary extracted tenant name across pages
            extracted_names = [
                p["expected_tenant_name"].strip()
                for p in raw_pages
                if p.get("expected_tenant_name") and p["expected_tenant_name"].strip()
            ]
            primary_name = Counter(extracted_names).most_common(1)[0][0] if extracted_names else None

            # Date normalization and nearest-neighbor inference
            valid_dates = []
            for idx, p in enumerate(raw_pages):
                r_date = normalize_date(p.get("raw_date"))
                p["resolved_date"] = r_date
                if r_date:
                    valid_dates.append((idx, r_date))

            if valid_dates:
                for idx, p in enumerate(raw_pages):
                    if not p.get("resolved_date"):
                        closest = min(valid_dates, key=lambda x: abs(x[0] - idx))
                        p["resolved_date"] = closest[1]

            # Match or insert tenants
            for p in raw_pages:
                t_name = (p.get("expected_tenant_name") or "").strip()
                if not t_name and primary_name:
                    t_name = primary_name

                assigned_tenant_id: Optional[int] = None
                if t_name:
                    key = t_name.lower()
                    if key in tenant_map:
                        assigned_tenant_id = tenant_map[key]
                    else:
                        # New tenant
                        s_date = p.get("resolved_date") or "1970-01-01"
                        new_t = repo.add_tenant(
                            house_id=clean_house_id,
                            name=t_name,
                            start_date=s_date,
                            end_date=None,
                        )
                        if new_t.id:
                            tenant_map[key] = new_t.id
                            assigned_tenant_id = new_t.id
                else:
                    if existing_tenants:
                        active_t = repo.get_active_tenant(clean_house_id, target_date=p.get("resolved_date"))
                        assigned_tenant_id = active_t.id if active_t else existing_tenants[0].id
                    else:
                        # Create default tenant
                        def_t = repo.add_tenant(
                            house_id=clean_house_id,
                            name="Default Tenant",
                            start_date="1970-01-01",
                            end_date=None,
                        )
                        if def_t.id:
                            tenant_map["default tenant"] = def_t.id
                            assigned_tenant_id = def_t.id

                p["tenant_id"] = assigned_tenant_id

            # Step f: Fine categorization per page
            for p in raw_pages:
                fine_cat, fine_reason = _resolve_fine_category(p, llm_client=llm_client, model=model)
                p["fine_category"] = fine_cat
                p["fine_category_reason"] = fine_reason

            # Step g: Bulk insert rows into pages table
            pages_to_add = []
            for p in raw_pages:
                pages_to_add.append({
                    "batch_id": batch_id,
                    "page_number": p["page_number"],
                    "house_id": clean_house_id,
                    "category": p.get("category"),
                    "content_explanation": p.get("content_explanation"),
                    "expected_tenant_name": p.get("expected_tenant_name"),
                    "expected_house_number": p.get("expected_house_number") or clean_house_id,
                    "raw_date": p.get("raw_date"),
                    "sender": p.get("sender"),
                    "receiver": p.get("receiver"),
                    "subject": p.get("subject"),
                    "is_continuation": bool(p.get("is_continuation", False)),
                    "tenant_id": p["tenant_id"],
                    "resolved_date": p["resolved_date"],
                    "fine_category": p.get("fine_category"),
                    "fine_category_reason": p.get("fine_category_reason"),
                    "vault_id": None,
                })

            repo.add_pages_bulk(pages_to_add)

            # Step h: Grouping & Slicing into vault
            grouped_docs = _group_pages_into_documents(raw_pages, clean_house_id)

            src_doc = fitz.open(str(target_batch_path))
            vault_ids: List[str] = []
            try:
                for d in grouped_docs:
                    vid = uuid.uuid4().hex
                    vault_ids.append(vid)

                    vault_pdf_filename = f"doc_{vid}.pdf"
                    vault_pdf_path = vault_dir / vault_pdf_filename

                    # Slice pages (fitz is 0-indexed, start/end are 1-indexed)
                    sub_doc = fitz.open()
                    sub_doc.insert_pdf(
                        src_doc,
                        from_page=d["start_page"] - 1,
                        to_page=d["end_page"] - 1,
                    )
                    sub_doc.save(str(vault_pdf_path))
                    sub_doc.close()
                    created_files.append(vault_pdf_path)

                    # Insert document row
                    repo.add_document(
                        vault_id=vid,
                        house_id=clean_house_id,
                        tenant_id=d["tenant_id"],
                        batch_id=batch_id,
                        primary_date=d["primary_date"],
                        arabic_title=d["arabic_title"],
                        category=d["category"],
                        page_count=d["page_count"],
                    )

                    # Link pages to document
                    conn.execute(
                        """
                        UPDATE pages
                        SET vault_id = ?
                        WHERE batch_id = ? AND page_number BETWEEN ? AND ?
                        """,
                        (vid, batch_id, d["start_page"], d["end_page"]),
                    )
            finally:
                src_doc.close()

            # Step i: Update batch status='completed'
            repo.update_batch_status(batch_id, "completed")

        logger.info(f"Successfully ingested batch {batch_id} for house {clean_house_id} ({len(grouped_docs)} docs created).")
        return {
            "status": "success",
            "batch_id": batch_id,
            "pages_ingested": total_pages,
            "documents_created": len(grouped_docs),
            "vault_ids": vault_ids,
            "house_id": clean_house_id,
            "area_id": area_id,
        }

    except Exception as e:
        logger.exception(f"Ingestion failed for {pdf_path.name}: {e}")
        # Clean up any created files on failure to avoid partial orphan files
        for f in created_files:
            if f.exists():
                try:
                    f.unlink()
                except OSError:
                    pass
        raise


def run_v11_ingest_mode(args: Any, config: Any, llm_client: Any) -> int:
    """Run CLI entry point for v11 database-backed ingestion.

    Args:
        args: Parsed CLI arguments.
        config: AppConfig instance.
        llm_client: Configured LLMClient instance.

    Returns:
        0 on success, 1 on failure.
    """
    input_path = Path(args.input_path).resolve()
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return 1

    areas_root = Path(getattr(args, "areas_root", None) or config.areas_root_path).resolve()
    db_path = Path(getattr(args, "db_path", None) or "file_organizer.db").resolve()
    dry_run = getattr(args, "dry_run", False)
    model = getattr(args, "model", None)

    pdf_files: List[Path] = []
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        pdf_files.append(input_path)
    elif input_path.is_dir():
        pdf_files.extend(sorted([p for p in input_path.glob("*.pdf") if not p.name.startswith("batch_") and not p.name.startswith("doc_")]))

    if not pdf_files:
        logger.warning(f"No valid PDF files found to ingest in {input_path}")
        return 0

    has_errors = False
    for pdf in pdf_files:
        # Determine house_id and area_id
        house_id = getattr(args, "house_id", None)
        area_id = getattr(args, "area_id", None)

        if not house_id:
            # Check if inside a house directory
            if pdf.parent.name.startswith("batch") or pdf.parent.name == "vault":
                house_id = extract_house_id(pdf.parent.parent.name)
            else:
                house_id = extract_house_id(pdf.parent.name)
                # If parent name is not house ID, fallback to PDF stem
                if not house_id or house_id == areas_root.name:
                    house_id = extract_house_id(pdf.stem)

        if not area_id:
            # Look at grandparent or parent directory
            if pdf.parent.parent.exists() and pdf.parent.parent.name != areas_root.name:
                area_id = pdf.parent.parent.name
            else:
                area_id = config.area_mappings.get(house_id, "Default Area") if hasattr(config, "area_mappings") else "Default Area"

        try:
            res = ingest_pdf_to_house(
                pdf_path=pdf,
                house_id=house_id,
                area_id=area_id,
                db_path=db_path,
                areas_root=areas_root,
                llm_client=llm_client,
                dry_run=dry_run,
                model=model,
            )
            logger.info(f"Ingestion result for {pdf.name}: {res}")
        except Exception as e:
            logger.exception(f"Failed to ingest {pdf.name}: {e}")
            has_errors = True

    return 1 if has_errors else 0
