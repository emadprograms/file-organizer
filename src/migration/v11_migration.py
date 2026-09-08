"""V11 Migration Engine.

Migrates legacy v5-v10 house data (directories containing .source_files/, state.json,
report.json, 1_tenants.yaml, .lnk shortcuts, Arabic category folders) into the
v11 SQLite database schema and clean two-folder on-disk structure:
    {area}/{house_id}/batches/
    {area}/{house_id}/vault/
"""

import json
import logging
import os
import re
import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import uuid

import yaml

from src.db.connection import get_db_connection
from src.db.models import Area, Batch, Document, House, Page, Tenant
from src.db.repository import Repository
from src.db.schema import init_db

logger = logging.getLogger(f"file_organizer.{__name__}")


def extract_house_id(name: str) -> str:
    """Extract clean house ID from directory or file name.
    
    Examples:
        '514 - محمد مبارك الشمري' -> '514'
        'H01 - Villa South' -> 'H01'
        '514' -> '514'
    """
    if " - " in name:
        return name.split(" - ", 1)[0].strip()
    return name.strip()


def normalize_date(val: Any) -> Optional[str]:
    """Normalize various date inputs to ISO format (YYYY-MM-DD) or None.
    
    Handles datetime/date objects, ISO strings, YYYY/MM/DD, DD-MM-YYYY,
    partial dates (YYYY-MM, YYYY), and common null-string markers ('NONE', 'present').
    """
    if not val:
        return None
    if isinstance(val, (date, datetime)):
        return val.strftime("%Y-%m-%d")
    if not isinstance(val, str):
        return None

    s = val.strip()
    if s.lower() in ("none", "nodate", "null", "present", "n/a", "-", ""):
        return None

    # YYYY-MM-DD or YYYY/MM/DD
    m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", s)
    if m:
        y, mth, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mth:02d}-{d:02d}"

    # DD-MM-YYYY or DD/MM/YYYY
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", s)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mth:02d}-{d:02d}"

    # YYYY-MM
    m = re.match(r"^(\d{4})[-/](\d{1,2})$", s)
    if m:
        y, mth = int(m.group(1)), int(m.group(2))
        return f"{y:04d}-{mth:02d}-01"

    # YYYY
    m = re.match(r"^(\d{4})$", s)
    if m:
        return f"{int(m.group(1)):04d}-01-01"

    return None


def get_pdf_page_count(pdf_path: Path) -> int:
    """Retrieve the number of pages in a PDF file using available libraries."""
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        return 1
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        count = len(doc)
        doc.close()
        return max(count, 1)
    except Exception:
        pass

    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        return max(len(reader.pages), 1)
    except Exception:
        pass

    return 1


def load_legacy_metadata(house_dir: Path, house_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
    """Locate and load legacy state.json and report.json files."""
    state_data: Optional[Dict[str, Any]] = None
    report_data: Optional[List[Dict[str, Any]]] = None

    candidate_state_paths = [
        house_dir / ".source_files" / f"{house_id}_state.json",
        house_dir / ".source_files" / "state.json",
        house_dir / f"{house_id}_state.json",
        house_dir / "state.json",
    ]
    for sp in candidate_state_paths:
        if sp.exists():
            try:
                with open(sp, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                break
            except Exception as e:
                logger.warning(f"Failed to read state file {sp}: {e}")

    candidate_report_paths = [
        house_dir / ".source_files" / f"{house_id}_report.json",
        house_dir / ".source_files" / "report.json",
        house_dir / f"{house_id}_report.json",
        house_dir / "report.json",
        house_dir / ".source_files" / f"{house_id}.raw_dump.json",
        house_dir / f"{house_id}.raw_dump.json",
    ]
    for rp in candidate_report_paths:
        if rp.exists():
            try:
                with open(rp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        report_data = data
                    elif isinstance(data, dict) and "per_page" in data:
                        report_data = data["per_page"]
                break
            except Exception as e:
                logger.warning(f"Failed to read report file {rp}: {e}")

    return state_data, report_data


def extract_tenants(
    house_dir: Path,
    house_id: str,
    state_data: Optional[Dict[str, Any]],
    report_data: Optional[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Extract tenant records from YAML, report.json, state.json, or directory name."""
    candidate_yaml_paths = [
        house_dir / ".source_files" / f"{house_id}_1_tenants.yaml",
        house_dir / ".source_files" / f"{house_id}_tenants.yaml",
        house_dir / ".source_files" / "1_tenants.yaml",
        house_dir / ".source_files" / "tenants.yaml",
        house_dir / f"{house_id}_1_tenants.yaml",
        house_dir / f"{house_id}_tenants.yaml",
        house_dir / "1_tenants.yaml",
        house_dir / "tenants.yaml",
    ]

    for yp in candidate_yaml_paths:
        if yp.exists():
            try:
                with open(yp, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, list) and data:
                    tenants = []
                    for item in data:
                        if isinstance(item, dict) and "name" in item:
                            t_name = str(item["name"]).strip()
                            s_date = normalize_date(item.get("start_date")) or "1970-01-01"
                            e_date = normalize_date(item.get("end_date"))
                            tenants.append({
                                "name": t_name,
                                "start_date": s_date,
                                "end_date": e_date,
                            })
                    if tenants:
                        return tenants
            except Exception as e:
                logger.warning(f"Error parsing tenant YAML {yp}: {e}")

    # Fallback to report.json or state.json
    found_names: List[str] = []
    if report_data:
        for item in report_data:
            name = item.get("tenant") or item.get("tenant_name") or item.get("expected_tenant_name")
            if name and str(name).strip() not in found_names:
                found_names.append(str(name).strip())

    if state_data:
        pages = (
            state_data.get("fine_categorized_pages")
            or state_data.get("cleaned_pages")
            or state_data.get("pages")
            or []
        )
        for p in pages:
            name = p.get("expected_tenant_name") or p.get("tenant")
            if name and str(name).strip() not in found_names:
                found_names.append(str(name).strip())

        docs = state_data.get("routed_documents") or state_data.get("grouped_documents") or []
        for d in docs:
            name = d.get("tenant") or d.get("tenant_name")
            if name and str(name).strip() not in found_names:
                found_names.append(str(name).strip())

    if found_names:
        return [{"name": name, "start_date": "1970-01-01", "end_date": None} for name in found_names]

    # Fallback to folder name
    if " - " in house_dir.name:
        folder_tenant = house_dir.name.split(" - ", 1)[1].strip()
        if folder_tenant:
            return [{"name": folder_tenant, "start_date": "1970-01-01", "end_date": None}]

    return [{"name": "Default Tenant", "start_date": "1970-01-01", "end_date": None}]


def find_raw_source_pdf(house_dir: Path, house_id: str) -> Optional[Path]:
    """Locate the master raw scan PDF for the house, avoiding vault documents."""
    # Check batches directory first (already migrated)
    batches_dir = house_dir / "batches"
    if batches_dir.exists():
        for f in batches_dir.glob("*.pdf"):
            if not f.name.startswith("doc_"):
                return f

    # Search top-level house directory and .source_files
    candidate_dirs = [house_dir, house_dir / ".source_files"]
    ignored_names = {"_finalized.pdf", "_raw_prepend.pdf", "_raw_append.pdf"}

    all_candidates: List[Path] = []
    for c_dir in candidate_dirs:
        if not c_dir.exists():
            continue
        for f in c_dir.glob("*.pdf"):
            if f.name.startswith("doc_"):
                continue
            if any(f.name.endswith(ign) for ign in ignored_names):
                continue
            all_candidates.append(f)

    if not all_candidates:
        return None

    # Prioritize files matching house_id
    for f in all_candidates:
        if f.stem == house_id or f.stem.startswith(f"{house_id}_"):
            return f

    return all_candidates[0]


def extract_documents_data(
    house_dir: Path,
    house_id: str,
    state_data: Optional[Dict[str, Any]],
    report_data: Optional[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Extract document metadata and discover all vault PDFs."""
    docs: List[Dict[str, Any]] = []
    seen_vids = set()

    sources: List[Dict[str, Any]] = []
    if state_data:
        sources.extend(state_data.get("routed_documents") or [])
        if not sources:
            sources.extend(state_data.get("grouped_documents") or [])
    if not sources and report_data:
        sources.extend(report_data)

    for item in sources:
        vid = item.get("vault_id")
        if not vid and "filename" in item:
            fn = item["filename"]
            if fn.startswith("doc_") and fn.endswith(".pdf"):
                vid = fn[4:-4]
        if not vid:
            vid = uuid.uuid4().hex

        if vid in seen_vids:
            continue
        seen_vids.add(vid)

        p_date = normalize_date(
            item.get("primary_date")
            or item.get("date")
            or (item.get("dates")[0] if item.get("dates") else None)
        )
        title = item.get("brief_arabic_title") or item.get("arabic_title") or item.get("title")
        # Use folder_path (the routed Arabic folder name, e.g. "صيانة", "عقود") as category.
        # This is what users see as "category" in the app. The 'category' field is the LLM
        # classification label ("letters", "forms", etc.) which is NOT the folder name.
        category = item.get("folder_path") or item.get("fine_category") or item.get("category")

        start_p = item.get("start_page")
        end_p = item.get("end_page")
        if start_p is not None and end_p is not None:
            p_count = max(int(end_p) - int(start_p) + 1, 1)
        else:
            p_count = int(item.get("page_count", 1))

        # primary_tenant is the canonical field in routed_documents.
        # 'tenant' and 'tenant_name' are often None there; they appear in other formats.
        tenant_name = (
            item.get("primary_tenant")
            or item.get("tenant")
            or item.get("tenant_name")
            or item.get("expected_tenant_name")
        )

        docs.append({
            "vault_id": str(vid),
            "primary_date": p_date,
            "arabic_title": title,
            "category": category,
            "page_count": p_count,
            "tenant_name": tenant_name,
            "start_page": int(start_p) if start_p is not None else None,
            "end_page": int(end_p) if end_p is not None else None,
        })

    # Discover on-disk vault files not yet in docs
    vault_dirs = [house_dir / ".source_files" / "vault", house_dir / "vault"]
    for v_dir in vault_dirs:
        if v_dir.exists():
            for vf in v_dir.glob("doc_*.pdf"):
                vid = vf.name[4:-4]
                if vid not in seen_vids:
                    seen_vids.add(vid)
                    cnt = get_pdf_page_count(vf)
                    docs.append({
                        "vault_id": vid,
                        "primary_date": None,
                        "arabic_title": None,
                        "category": None,
                        "page_count": cnt,
                        "tenant_name": None,
                        "start_page": None,
                        "end_page": None,
                    })

    return docs


def extract_pages_data(
    house_id: str,
    state_data: Optional[Dict[str, Any]],
    report_data: Optional[List[Dict[str, Any]]],
    documents_data: List[Dict[str, Any]],
    total_batch_pages: int,
) -> List[Dict[str, Any]]:
    """Extract per-page records from state.json, report.json, or documents."""
    pages: List[Dict[str, Any]] = []

    raw_pages = []
    if state_data:
        raw_pages = (
            state_data.get("fine_categorized_pages")
            or state_data.get("cleaned_pages")
            or state_data.get("pages")
            or []
        )

    if raw_pages:
        for idx, p in enumerate(raw_pages):
            orig_idx = p.get("original_index")
            if orig_idx is None:
                orig_idx = p.get("page_index")

            if orig_idx is not None:
                page_num = int(orig_idx) + 1
            elif p.get("page_number") is not None:
                page_num = int(p["page_number"])
            else:
                page_num = idx + 1

            r_date = normalize_date(p.get("resolved_date") or p.get("date"))
            raw_d = p.get("raw_date") or (p.get("dates")[0] if p.get("dates") else None)

            pages.append({
                "page_number": page_num,
                "category": p.get("category"),
                "content_explanation": p.get("content_explanation"),
                "expected_tenant_name": p.get("expected_tenant_name") or p.get("tenant"),
                "expected_house_number": str(p.get("expected_house_number") or house_id),
                "raw_date": raw_d,
                "sender": p.get("sender"),
                "receiver": p.get("receiver"),
                "subject": p.get("subject"),
                "is_continuation": bool(p.get("is_continuation", False)),
                "resolved_date": r_date,
                "fine_category": p.get("fine_category"),
                "fine_category_reason": p.get("fine_category_reason"),
                "vault_id": p.get("vault_id"),
            })
    elif documents_data:
        current_page = 1
        for doc in documents_data:
            s_page = doc.get("start_page") or current_page
            e_page = doc.get("end_page") or (s_page + doc.get("page_count", 1) - 1)
            for p_num in range(s_page, e_page + 1):
                pages.append({
                    "page_number": p_num,
                    "category": doc.get("category"),
                    "content_explanation": doc.get("arabic_title"),
                    "expected_tenant_name": doc.get("tenant_name"),
                    "expected_house_number": str(house_id),
                    "raw_date": doc.get("primary_date"),
                    "sender": None,
                    "receiver": None,
                    "subject": doc.get("arabic_title"),
                    "is_continuation": (p_num > s_page),
                    "resolved_date": doc.get("primary_date"),
                    "fine_category": doc.get("category"),
                    "fine_category_reason": None,
                    "vault_id": doc.get("vault_id"),
                })
            current_page = max(current_page, e_page + 1)
    else:
        for p_num in range(1, total_batch_pages + 1):
            pages.append({
                "page_number": p_num,
                "category": None,
                "content_explanation": None,
                "expected_tenant_name": None,
                "expected_house_number": str(house_id),
                "raw_date": None,
                "sender": None,
                "receiver": None,
                "subject": None,
                "is_continuation": False,
                "resolved_date": None,
                "fine_category": None,
                "fine_category_reason": None,
                "vault_id": None,
            })

    # Link page vault_id if start_page/end_page matches
    for p in pages:
        if not p.get("vault_id"):
            p_num = p["page_number"]
            for d in documents_data:
                s_p = d.get("start_page")
                e_p = d.get("end_page")
                if s_p is not None and e_p is not None and s_p <= p_num <= e_p:
                    p["vault_id"] = d["vault_id"]
                    break

    return pages


def migrate_house_to_v11(
    house_dir: Union[Path, str],
    area_id: str,
    db_path: Union[Path, str] = "file_organizer.db",
    area_code: Optional[str] = None,
    dry_run: bool = False,
    rename_folder: bool = True,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Migrate a single house directory to v11 database and storage structure.
    
    Args:
        house_dir: Path to the house directory.
        area_id: ID of the area (e.g. 'Safra C').
        db_path: Path to the SQLite database.
        area_code: Optional code for the area (e.g. 'SAF C').
        dry_run: If True, do not modify files or commit database transactions.
        rename_folder: If True, rename house folder to clean house ID (e.g. '514').
        conn: Optional existing database connection.
        
    Returns:
        Dict with migration results and counts.
    """
    house_path = Path(house_dir).resolve()
    if not house_path.exists():
        raise FileNotFoundError(f"House directory does not exist: {house_path}")

    house_id = extract_house_id(house_path.name)
    logger.info(f"Starting migration for house '{house_id}' ({house_path.name}) in area '{area_id}'")

    state_data, report_data = load_legacy_metadata(house_path, house_id)
    raw_pdf_path = find_raw_source_pdf(house_path, house_id)
    extracted_tenants = extract_tenants(house_path, house_id, state_data, report_data)
    extracted_docs = extract_documents_data(house_path, house_id, state_data, report_data)

    if raw_pdf_path:
        batch_page_count = get_pdf_page_count(raw_pdf_path)
        batch_filename = (
            raw_pdf_path.name
            if raw_pdf_path.name.startswith("batch_")
            else f"batch_1_{raw_pdf_path.name}"
        )
    else:
        batch_page_count = max(sum(d.get("page_count", 1) for d in extracted_docs), 1)
        batch_filename = f"batch_1_{house_id}.pdf"

    extracted_pages = extract_pages_data(
        house_id, state_data, report_data, extracted_docs, batch_page_count
    )

    if dry_run:
        logger.info(f"[DRY RUN] Previewing migration for {house_id}: {len(extracted_tenants)} tenants, {len(extracted_docs)} docs, {len(extracted_pages)} pages.")
        return {
            "status": "success",
            "dry_run": True,
            "house_id": house_id,
            "area_id": area_id,
            "tenants_migrated": len(extracted_tenants),
            "batches_migrated": 1,
            "documents_migrated": len(extracted_docs),
            "pages_migrated": len(extracted_pages),
            "target_house_dir": house_path.parent / (house_id if rename_folder else house_path.name),
        }

    # Open DB connection if not passed
    close_conn = False
    if conn is None:
        conn = get_db_connection(db_path)
        init_db(conn)
        close_conn = True

    try:
        repo = Repository(conn, autocommit=False)

        # 1. Area
        existing_area = repo.get_area(area_id)
        if not existing_area:
            repo.add_area(area_id=area_id, code=area_code)
        elif area_code and not existing_area.code:
            conn.execute("UPDATE areas SET code = ? WHERE id = ?", (area_code, area_id))

        # 2. House
        existing_house = repo.get_house(house_id)
        if not existing_house:
            repo.add_house(house_id=house_id, area_id=area_id)

        # 3. Tenants
        existing_tenants = repo.list_tenants_by_house(house_id)
        tenant_map: Dict[str, int] = {t.name.strip().lower(): t.id for t in existing_tenants if t.id}
        for t_info in extracted_tenants:
            t_name = t_info["name"].strip()
            if t_name.lower() == "default tenant" and existing_tenants:
                continue
            key = t_name.lower()
            if key not in tenant_map:
                created_t = repo.add_tenant(
                    house_id=house_id,
                    name=t_name,
                    start_date=t_info["start_date"],
                    end_date=t_info["end_date"],
                )
                if created_t.id:
                    tenant_map[key] = created_t.id

        default_tenant_id = (
            existing_tenants[0].id
            if existing_tenants and existing_tenants[0].id
            else (list(tenant_map.values())[0] if tenant_map else None)
        )
        if default_tenant_id is None:
            created_def = repo.add_tenant(
                house_id=house_id,
                name="Default Tenant",
                start_date="1970-01-01",
                end_date=None,
            )
            default_tenant_id = created_def.id

        # 4. Batch
        existing_batches = repo.list_batches_by_house(house_id)
        if existing_batches:
            batch = existing_batches[0]
        else:
            batch = repo.create_batch(
                house_id=house_id,
                filename=batch_filename,
                file_path=f"batches/{batch_filename}",
                page_count=batch_page_count,
                status="completed",
            )
        batch_id = batch.id
        assert batch_id is not None

        # 5. Documents
        for d in extracted_docs:
            vid = d["vault_id"]
            if not repo.get_document(vid):
                t_id = default_tenant_id
                if d.get("tenant_name"):
                    t_key = d["tenant_name"].strip().lower()
                    t_id = tenant_map.get(t_key, default_tenant_id)
                repo.add_document(
                    vault_id=vid,
                    house_id=house_id,
                    tenant_id=t_id,  # type: ignore
                    batch_id=batch_id,
                    primary_date=d.get("primary_date"),
                    arabic_title=d.get("arabic_title"),
                    category=d.get("category"),
                    page_count=d.get("page_count", 1),
                )

        # 6. Pages
        existing_pages = repo.get_pages_by_batch(batch_id)
        existing_p_nums = {p.page_number for p in existing_pages}
        pages_to_add = []
        for p in extracted_pages:
            p_num = p["page_number"]
            if p_num in existing_p_nums:
                continue

            t_id = default_tenant_id
            if p.get("expected_tenant_name"):
                t_key = p["expected_tenant_name"].strip().lower()
                t_id = tenant_map.get(t_key, default_tenant_id)

            v_id = p.get("vault_id")
            if v_id and not repo.get_document(v_id):
                v_id = None

            pages_to_add.append({
                "batch_id": batch_id,
                "page_number": p_num,
                "house_id": house_id,
                "category": p.get("category"),
                "content_explanation": p.get("content_explanation"),
                "expected_tenant_name": p.get("expected_tenant_name"),
                "expected_house_number": p.get("expected_house_number"),
                "raw_date": p.get("raw_date"),
                "sender": p.get("sender"),
                "receiver": p.get("receiver"),
                "subject": p.get("subject"),
                "is_continuation": p.get("is_continuation", False),
                "tenant_id": t_id,
                "resolved_date": p.get("resolved_date"),
                "fine_category": p.get("fine_category"),
                "fine_category_reason": p.get("fine_category_reason"),
                "vault_id": v_id,
            })

        if pages_to_add:
            repo.add_pages_bulk(pages_to_add)

        # Commit all DB operations
        conn.commit()

        # 7. Physical Disk Restructuring
        target_vault = house_path / "vault"
        target_batches = house_path / "batches"
        target_vault.mkdir(parents=True, exist_ok=True)
        target_batches.mkdir(parents=True, exist_ok=True)

        # Move vault files from .source_files/vault to vault/
        source_vault = house_path / ".source_files" / "vault"
        if source_vault.exists():
            for vf in list(source_vault.glob("*.pdf")):
                dest = target_vault / vf.name
                if not dest.exists():
                    shutil.move(str(vf), str(dest))

        # Move raw master PDF into batches/ (only if one actually exists).
        # The batch PDF is a UX convenience (a merged scan of all vault docs) — it is NOT
        # required for migration. The DB batch record captures the metadata.
        # We never create blank placeholder PDFs; that would produce garbage files.
        dest = target_batches / batch_filename
        if raw_pdf_path and raw_pdf_path.exists():
            if raw_pdf_path.resolve() != dest.resolve():
                if dest.exists():
                    raw_pdf_path.unlink()
                else:
                    shutil.move(str(raw_pdf_path), str(dest))
        # No else — if there's no raw scan, leave batches/ empty; the PDF can be
        # generated later by merging vault docs if desired.

        # Remove shortcuts (*.lnk)
        for lnk in list(house_path.rglob("*.lnk")):
            try:
                lnk.unlink()
            except Exception as e:
                logger.warning(f"Could not remove shortcut {lnk}: {e}")

        # Clean legacy directories (excluding vault and batches)
        protected_dirs = {"vault", "batches"}
        for item in list(house_path.iterdir()):
            if item.is_dir() and item.name not in protected_dirs:
                shutil.rmtree(str(item), ignore_errors=True)
            elif item.is_file() and not item.name.startswith("."):
                if item.suffix.lower() in (".json", ".yaml", ".yml", ".txt", ".bak"):
                    try:
                        item.unlink()
                    except Exception:
                        pass

        # House folder renaming
        target_house_dir = house_path
        if rename_folder and house_path.name != house_id:
            dest_dir = house_path.parent / house_id
            if dest_dir.exists() and dest_dir != house_path:
                logger.warning(f"Renaming skipped: target {dest_dir} already exists.")
                target_house_dir = dest_dir
            elif dest_dir == house_path:
                target_house_dir = dest_dir
            else:
                try:
                    house_path.rename(dest_dir)
                    target_house_dir = dest_dir
                except PermissionError as e:
                    # Common on SMB/network volumes — not a fatal error, DB is already committed.
                    logger.warning(
                        f"Could not rename '{house_path.name}' → '{house_id}': {e}. "
                        "Folder retains original name; migration data is complete."
                    )
                    target_house_dir = house_path

        logger.info(f"Migration completed successfully for house '{house_id}'.")
        return {
            "status": "success",
            "dry_run": False,
            "house_id": house_id,
            "area_id": area_id,
            "tenants_migrated": len(repo.list_tenants_by_house(house_id)),
            "batches_migrated": 1,
            "documents_migrated": len(repo.list_documents_by_house(house_id)),
            "pages_migrated": len(repo.get_pages_by_batch(batch_id)),
            "target_house_dir": target_house_dir,
        }
    finally:
        if close_conn:
            conn.close()


def migrate_areas(
    areas_root_path: Union[Path, str],
    db_path: Union[Path, str] = "file_organizer.db",
    area_mappings: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    rename_folder: bool = True,
    target_house: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> List[Dict[str, Any]]:
    """Migrate all houses across area directories under areas_root_path.
    
    Args:
        areas_root_path: Path to the root areas directory.
        db_path: Path to SQLite database.
        area_mappings: Mapping of area names to area codes (e.g. {'Safra C': 'SAF C'}).
        dry_run: If True, do not modify files or write to DB.
        rename_folder: If True, rename house folders to ID.
        target_house: Optional house ID filter to migrate only one house.
        conn: Optional existing DB connection.
        
    Returns:
        List of migration result dicts for each house.
    """
    root = Path(areas_root_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Areas root directory not found: {root}")

    area_mappings = area_mappings or {}
    results = []

    close_conn = False
    if conn is None:
        conn = get_db_connection(db_path)
        init_db(conn)
        close_conn = True

    try:
        # Find area directories
        for area_dir in sorted(root.iterdir()):
            if not area_dir.is_dir() or area_dir.name.startswith("."):
                continue

            area_name = area_dir.name
            area_code = area_mappings.get(area_name)

            for house_item in sorted(area_dir.iterdir()):
                if not house_item.is_dir() or house_item.name.startswith("."):
                    continue

                hid = extract_house_id(house_item.name)
                if target_house and hid != target_house:
                    continue

                try:
                    res = migrate_house_to_v11(
                        house_dir=house_item,
                        area_id=area_name,
                        db_path=db_path,
                        area_code=area_code,
                        dry_run=dry_run,
                        rename_folder=rename_folder,
                        conn=conn,
                    )
                    results.append(res)
                except Exception as e:
                    logger.exception(f"Failed to migrate house {house_item}: {e}")
                    results.append({
                        "status": "error",
                        "house_id": hid,
                        "area_id": area_name,
                        "error": str(e),
                    })
    finally:
        if close_conn:
            conn.close()

    return results


def verify_migration_integrity(
    house_dir: Union[Path, str],
    house_id: str,
    repo: Repository,
) -> Dict[str, Any]:
    """Verify that every database record has an accessible physical file on disk.
    
    Args:
        house_dir: Path to the migrated house directory.
        house_id: ID of the house.
        repo: Repository instance connected to the database.
        
    Returns:
        Dict with 'is_valid' boolean and list of 'errors'.
    """
    h_path = Path(house_dir).resolve()
    errors: List[str] = []

    house = repo.get_house(house_id)
    if not house:
        errors.append(f"House '{house_id}' not found in database.")
        return {"is_valid": False, "errors": errors}

    # Verify vault documents
    vault_dir = h_path / "vault"
    docs = repo.list_documents_by_house(house_id)
    for doc in docs:
        expected_pdf = vault_dir / f"doc_{doc.vault_id}.pdf"
        if not expected_pdf.exists():
            errors.append(f"Missing physical file for document '{doc.vault_id}': {expected_pdf}")
        elif expected_pdf.stat().st_size == 0:
            errors.append(f"Physical file for document '{doc.vault_id}' is empty: {expected_pdf}")

    # Verify batches
    batches_dir = h_path / "batches"
    batches = repo.list_batches_by_house(house_id)
    for b in batches:
        b_file = h_path / b.file_path
        if not b_file.exists():
            # Check batches directory fallback
            alt_b_file = batches_dir / b.filename
            if not alt_b_file.exists():
                errors.append(f"Missing physical file for batch '{b.id}': {b_file}")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "documents_checked": len(docs),
        "batches_checked": len(batches),
    }
