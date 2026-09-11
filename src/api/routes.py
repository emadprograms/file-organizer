import os
import json
import base64
import re
import difflib
import time
import shutil
import uuid
import tempfile
import unicodedata
import io
import zipfile
import urllib.parse
import fitz
import arabic_reshaper
from bidi.algorithm import get_display
from pathlib import Path
from datetime import date, datetime
from typing import Optional, Union, Any
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import ValidationError

from src.api.models import (
    HouseResponse,
    VaultFileResponse,
    CategoryResponse,
    TimelineGroupResponse,
    TreeItemResponse,
    SearchResultResponse,
    TenantItem,
    TenantBulkUpdateRequest,
    TenantReallocationResponse,
    DocumentTenantUpdateRequest,
    DocumentNotesRequest,
    DocumentNotesResponse,
    DocumentUpdateRequest,
    DocumentCopyRequest,
    DocumentActionResponse,
    HouseTenantProfile,
    CategoryBreakdownItem,
    HouseArchiveProfile,
    HouseProfileResponse,
    IngestResponse,
    AIPreviewResponse,
    BatchDeleteRequest,
    BatchDeleteResponse,
    BatchMoveRequest,
    BatchMoveResponse,
    BatchCopyRequest,
    BatchCopyResponse,
    CreateHouseRequest,
    CreateHouseResponse,
)
from src.db.repository import (
    Repository,
    get_or_create_numbered_folder,
    update_document,
    copy_document,
    batch_copy_documents,
    reset_document_manual_lock,
    delete_document,
)
from src.migration.v11_migration import extract_house_id, normalize_date
from src.ingest.manual_ingest import ingest_document_manual
from src.ingest.v11_ingest import ingest_pdf_to_house

router = APIRouter()

NOT_FOUND_DETAIL = "{\"error\": \"Resource not found.\", \"solution\": \"Verify the endpoint URL and the resource ID.\"}"

def _house_sort_key_str(house_id: str) -> tuple[int, str]:
    match = re.search(r'(\d+)', house_id)
    num = int(match.group(1)) if match else 999999999
    return (num, house_id)

def get_db_repo(request: Request) -> Optional[Repository]:
    repo = getattr(request.app.state, "repo", None)
    if repo is not None:
        try:
            repo.conn.execute("SELECT 1")
            return repo
        except Exception:
            request.app.state.repo = None
            repo = None

    conn = getattr(request.app.state, "db_conn", None)
    if conn is not None:
        try:
            conn.execute("SELECT 1")
            repo = Repository(conn)
            request.app.state.repo = repo
            return repo
        except Exception:
            request.app.state.db_conn = None

    config = getattr(request.app.state, "config", None)
    db_path = getattr(request.app.state, "db_path", None) or (getattr(config, "db_path", None) if config else None)
    if db_path and (db_path == ":memory:" or Path(db_path).exists()):
        try:
            from src.db.connection import get_db_connection
            from src.db.schema import init_db
            conn = get_db_connection(db_path)
            init_db(conn)
            conn.execute("SELECT 1")
            repo = Repository(conn)
            request.app.state.repo = repo
            return repo
        except Exception:
            return None
    return None

from src.core.text_utils import clean_article, phonetic_normalize, score_tenant_match


def validate_id(id_str: str, pattern: str) -> None:
    if not re.match(pattern, id_str):
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)


def _get_document_groups(state_data: dict) -> list[dict]:
    routed = state_data.get("routed_documents", [])
    if isinstance(routed, list) and routed and routed[0].get("vault_id"):
        return routed
    grouped = state_data.get("grouped_documents", [])
    if isinstance(grouped, list) and grouped and grouped[0].get("vault_id"):
        return grouped
    if isinstance(grouped, list) and grouped:
        return grouped
    if isinstance(routed, list) and routed:
        return routed
    return []


@router.get("/api/houses", response_model=list[HouseResponse])
async def list_houses(request: Request):
    repo = get_db_repo(request)
    if repo:
        cursor = repo.conn.execute("SELECT id FROM houses ORDER BY id")
        rows = cursor.fetchall()
        if rows:
            return [HouseResponse(id=row["id"], name=row["id"]) for row in rows]

    config = getattr(request.app.state, "config", None)
    if not config or not hasattr(config, "areas_root_path"):
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    areas_root = Path(config.areas_root_path)
    if not areas_root.exists():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    
    houses = []
    for entry in areas_root.iterdir():
        if entry.is_dir():
            houses.append(HouseResponse(id=entry.name, name=entry.name))
    return houses

@router.get("/api/houses/{house_id}/vault", response_model=list[VaultFileResponse])
async def list_vault_files(request: Request, house_id: str):
    validate_id(house_id, r"^[a-zA-Z0-9_\-\s]+$")
    repo = get_db_repo(request)
    if repo:
        house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
        cursor = repo.conn.execute("""
            SELECT d.vault_id, d.primary_date, d.arabic_title, d.category, d.page_count, d.is_manual, d.tenant_id, t.name as tenant_name, b.filename
            FROM documents d
            LEFT JOIN tenants t ON d.tenant_id = t.id
            LEFT JOIN batches b ON d.batch_id = b.id
            WHERE d.house_id = ? OR d.house_id = ?
            ORDER BY d.primary_date DESC
        """, (house_id, house_num))
        rows = cursor.fetchall()
        if rows:
            return [
                VaultFileResponse(
                    vault_id=r["vault_id"],
                    filename=r["filename"] or f"doc_{r['vault_id']}.pdf",
                    start_page=1,
                    end_page=r["page_count"] or 1,
                    date=str(r["primary_date"]) if r["primary_date"] else "",
                    tenant=r["tenant_name"] or "",
                    tenant_id=r["tenant_id"],
                    category=r["category"] or "",
                    brief_arabic_title=r["arabic_title"] or "",
                    is_manual=int(r["is_manual"] or 0)
                )
                for r in rows
            ]

    config = getattr(request.app.state, "config", None)
    if not config or not hasattr(config, "areas_root_path"):
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    areas_root = Path(config.areas_root_path)
    report_path = areas_root / house_id / ".source_files" / f"{house_id}_report.json"
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
        
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
    except Exception:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
        
    responses = []
    for doc in report_data.get("documents", []):
        try:
            responses.append(VaultFileResponse(
                vault_id=doc.get("vault_id", ""),
                filename=doc.get("source_pdf", ""),
                start_page=doc.get("start_page", 0),
                end_page=doc.get("end_page", 0),
                date=doc.get("dates", [""])[0] if doc.get("dates") else "",
                tenant=doc.get("primary_tenant", "") or ""
            ))
        except ValidationError:
            pass
    return responses


def _get_areas_root_path(request: Request) -> Path:
    config = getattr(request.app.state, "config", None)
    if config and getattr(config, "areas_root_path", None):
        return Path(config.areas_root_path)
    if hasattr(request.app.state, "areas_root_path") and request.app.state.areas_root_path:
        return Path(request.app.state.areas_root_path)
    if hasattr(request.app.state, "areas_root") and request.app.state.areas_root:
        return Path(request.app.state.areas_root)
    return Path("areas")


@router.post("/api/areas/{area_id}/houses", response_model=CreateHouseResponse)
async def create_house(request: Request, area_id: str, payload: CreateHouseRequest):
    if not payload.house_id or not payload.house_id.strip():
        raise HTTPException(status_code=400, detail="House ID is required and cannot be empty.")

    clean_house_id = payload.house_id.strip()
    clean_area_id = (payload.area_id.strip() if (payload.area_id and payload.area_id.strip()) else area_id.strip())

    if not clean_area_id or clean_area_id == "{area_id}":
        raise HTTPException(status_code=400, detail="Area ID is required and cannot be empty.")

    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=503, detail="Database not connected.")

    existing = repo.get_house(clean_house_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"House '{clean_house_id}' already exists in area '{existing.area_id}'."
        )

    if not repo.get_area(clean_area_id):
        repo.add_area(area_id=clean_area_id)

    repo.add_house(house_id=clean_house_id, area_id=clean_area_id)

    tenant_id = None
    if payload.initial_tenant_name and payload.initial_tenant_name.strip():
        s_date = payload.start_date.strip() if (payload.start_date and payload.start_date.strip()) else date.today().isoformat()
        tenant = repo.add_tenant(
            house_id=clean_house_id,
            name=payload.initial_tenant_name.strip(),
            start_date=s_date,
        )
        tenant_id = tenant.id

    if not repo.autocommit:
        repo.conn.commit()

    areas_root = _get_areas_root_path(request)
    batches_dir = areas_root / clean_area_id / clean_house_id / "batches"
    vault_dir = areas_root / clean_area_id / clean_house_id / "vault"
    batches_dir.mkdir(parents=True, exist_ok=True)
    vault_dir.mkdir(parents=True, exist_ok=True)

    clear_tree_cache()

    return CreateHouseResponse(
        status="success",
        area_id=clean_area_id,
        house_id=clean_house_id,
        tenant_id=tenant_id,
        message=f"House '{clean_house_id}' registered successfully in area '{clean_area_id}'."
    )


@router.delete("/api/areas/{area_id}/houses/{house_id}")
async def delete_house_endpoint(request: Request, area_id: str, house_id: str):
    clean_house_id = house_id.strip()
    clean_area_id = area_id.strip()
    if not clean_house_id:
        raise HTTPException(status_code=400, detail="House ID is required and cannot be empty.")

    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=503, detail="Database not connected.")

    areas_root = _get_areas_root_path(request)
    deleted = repo.delete_house(clean_house_id, clean_area_id, areas_root)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"House '{clean_house_id}' not found in area '{clean_area_id}'.")

    clear_tree_cache()
    return {"status": "success", "message": f"House '{clean_house_id}' deleted successfully."}


@router.get("/api/areas/{area_id}/houses/{house_id}/timeline", response_model=list[TimelineGroupResponse])
async def list_timeline(request: Request, area_id: str, house_id: str):
    repo = get_db_repo(request)
    if repo:
        conn = repo.conn
        house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
        cursor = conn.execute("""
            SELECT d.vault_id, d.primary_date, d.arabic_title, d.category, d.is_manual, d.tenant_id, d.notes, t.name as tenant_name
            FROM documents d
            LEFT JOIN tenants t ON d.tenant_id = t.id
            WHERE (d.house_id = ? OR d.house_id = ?) AND (d.is_timeline_visible IS NULL OR d.is_timeline_visible = 1)
            ORDER BY d.primary_date DESC
        """, (house_id, house_num))
        rows = cursor.fetchall()
        if rows:
            return [
                TimelineGroupResponse(
                    vault_id=r["vault_id"],
                    primary_tenant=r["tenant_name"] or "",
                    tenant_id=r["tenant_id"],
                    dates=[str(r["primary_date"])] if r["primary_date"] else [],
                    brief_arabic_title=r["arabic_title"] or "",
                    category=r["category"] or "",
                    is_manual=int(r["is_manual"] or 0),
                    notes=r["notes"]
                )
                for r in rows
            ]
        # Check if house exists in DB
        h_cur = conn.execute("SELECT id FROM houses WHERE id = ? OR id = ?", (house_id, house_num))
        if h_cur.fetchone():
            return []

    config = getattr(request.app.state, "config", None)
    if not config or not hasattr(config, "areas_root_path"):
        return []
    areas_root = Path(config.areas_root_path)
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    state_path = areas_root / area_id / house_id / ".source_files" / f"{house_num}_state.json"

    responses = []
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state_data = json.load(f)
        except Exception:
            raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

        for group in _get_document_groups(state_data):
            try:
                responses.append(TimelineGroupResponse(
                    vault_id=group.get("vault_id", ""),
                    primary_tenant=group.get("primary_tenant", "") or "",
                    dates=group.get("dates", []),
                    brief_arabic_title=group.get("brief_arabic_title", "")
                ))
            except ValidationError:
                pass
    else:
        house_entry = areas_root / area_id / house_id
        if house_entry.exists():
            for tenant_dir in house_entry.iterdir():
                if tenant_dir.is_dir() and tenant_dir.name != ".source_files":
                    m = re.match(r'^(.*?)\s*‎?\((.*?)\)‎?$', tenant_dir.name)
                    t_name = m.group(1).strip() if m else tenant_dir.name
                    for cat_dir in tenant_dir.iterdir():
                        if cat_dir.is_dir():
                            for doc_file in cat_dir.glob("*.pdf"):
                                doc_m = re.match(r'^(\d{4}-\d{2}-\d{2})\s*-\s*(.*?)\.pdf$', doc_file.name)
                                date_str = doc_m.group(1) if doc_m else ""
                                title = doc_m.group(2) if doc_m else doc_file.stem
                                rel_path = str(doc_file.relative_to(house_entry))
                                encoded = base64.urlsafe_b64encode(rel_path.encode('utf-8')).decode('utf-8').rstrip("=")
                                responses.append(TimelineGroupResponse(
                                    vault_id=f"fs_{encoded}",
                                    primary_tenant=t_name,
                                    dates=[date_str] if date_str else [],
                                    brief_arabic_title=title
                                ))

    def get_sort_date(r: TimelineGroupResponse) -> str:
        if r.dates and r.dates[0] and r.dates[0] != "NONE":
            return r.dates[0]
        return "0000-00-00"
        
    responses.sort(key=get_sort_date, reverse=True)
    return responses


def _format_arabic_duration(start_date_str: str, end_date_str: str | None = None) -> tuple[int, str]:
    """Calculate duration in years and format an Arabic description."""
    try:
        start_d = datetime.strptime(start_date_str[:10], "%Y-%m-%d").date()
    except Exception:
        return 0, ""
    
    if end_date_str:
        try:
            end_d = datetime.strptime(end_date_str[:10], "%Y-%m-%d").date()
        except Exception:
            end_d = date.today()
        is_active = False
    else:
        end_d = date.today()
        is_active = True

    days = max((end_d - start_d).days, 0)
    years_int = int(round(days / 365.25))

    start_yr = start_d.year
    if is_active:
        if years_int <= 0:
            dur_str = f"بدء الإيجار {start_yr} (مستمر منذ أقل من سنة)"
        elif years_int == 1:
            dur_str = f"بدء الإيجار {start_yr} (مستمر منذ سنة واحدة)"
        elif years_int == 2:
            dur_str = f"بدء الإيجار {start_yr} (مستمر منذ سنتين)"
        elif 3 <= years_int <= 10:
            dur_str = f"بدء الإيجار {start_yr} (مستمر منذ {years_int} سنوات)"
        else:
            dur_str = f"بدء الإيجار {start_yr} (مستمر منذ {years_int} سنة)"
    else:
        end_yr = end_d.year
        if years_int <= 0:
            dur_str = f"فترة الإيجار: {start_yr} (أقل من سنة)"
        elif years_int == 1:
            dur_str = f"فترة الإيجار: {start_yr} – {end_yr} (سنة واحدة)"
        elif years_int == 2:
            dur_str = f"فترة الإيجار: {start_yr} – {end_yr} (سنتان)"
        elif 3 <= years_int <= 10:
            dur_str = f"فترة الإيجار: {start_yr} – {end_yr} ({years_int} سنوات)"
        else:
            dur_str = f"فترة الإيجار: {start_yr} – {end_yr} ({years_int} سنة)"

    return years_int, dur_str


def _format_arabic_timespan(oldest_str: str | None, newest_str: str | None) -> tuple[int, str]:
    if not oldest_str or not newest_str:
        return 0, "لا توجد وثائق مسجلة"
    try:
        d1 = datetime.strptime(oldest_str[:10], "%Y-%m-%d").date()
        d2 = datetime.strptime(newest_str[:10], "%Y-%m-%d").date()
    except Exception:
        return 0, f"من {oldest_str} إلى {newest_str}"
    
    if d1 > d2:
        d1, d2 = d2, d1
    
    years = max(int(round((d2 - d1).days / 365.25)), 1) if (d2 - d1).days > 180 else 0
    y1, y2 = d1.year, d2.year
    if y1 == y2:
        return 1, f"سجلات عام {y1}"
    
    if years <= 1:
        return 1, f"من {y1} إلى {y2} (سنة واحدة)"
    elif years == 2:
        return 2, f"من {y1} إلى {y2} (سنتان)"
    elif 3 <= years <= 10:
        return years, f"من {y1} إلى {y2} ({years} سنوات)"
    else:
        return years, f"من {y1} إلى {y2} ({years} سنة)"


@router.get("/api/areas/{area_id}/houses/{house_id}/profile", response_model=HouseProfileResponse)
async def get_house_profile(request: Request, area_id: str, house_id: str):
    repo = get_db_repo(request)
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id

    if repo:
        conn = repo.conn
        h_cur = conn.execute("SELECT id FROM houses WHERE id = ? OR id = ?", (house_id, house_num))
        h_row = h_cur.fetchone()
        if not h_row:
            raise HTTPException(status_code=404, detail="House not found.")
        db_house_id = h_row["id"]

        tenants_db = repo.list_tenants_by_house(db_house_id)

        doc_cursor = conn.execute("""
            SELECT vault_id, tenant_id, primary_date, category, page_count, batch_id
            FROM documents
            WHERE house_id = ?
        """, (db_house_id,))
        docs = doc_cursor.fetchall()

        batch_cursor = conn.execute("SELECT id, page_count FROM batches WHERE house_id = ?", (db_house_id,))
        batches = batch_cursor.fetchall()

        tenant_doc_counts = {}
        tenant_cat_sets = {}
        for d in docs:
            tid = d["tenant_id"]
            tenant_doc_counts[tid] = tenant_doc_counts.get(tid, 0) + 1
            if tid not in tenant_cat_sets:
                tenant_cat_sets[tid] = set()
            if d["category"]:
                tenant_cat_sets[tid].add(d["category"])

        tenant_profiles = []
        for t in tenants_db:
            is_active = (t.end_date is None)
            y_int, dur_str = _format_arabic_duration(str(t.start_date), str(t.end_date) if t.end_date else None)
            t_dur_cat = "short" if y_int < 5 else ("medium" if y_int <= 10 else "long")
            tenant_profiles.append(HouseTenantProfile(
                id=t.id,
                name=t.name,
                start_date=str(t.start_date),
                end_date=str(t.end_date) if t.end_date else None,
                is_active=is_active,
                duration_str_ar=dur_str,
                duration_category=t_dur_cat,
                document_count=tenant_doc_counts.get(t.id, 0),
                category_count=len(tenant_cat_sets.get(t.id, set())),
            ))

        tenant_profiles.sort(key=lambda x: (not x.is_active, x.start_date), reverse=False)

        valid_dates = [str(d["primary_date"]) for d in docs if d["primary_date"] and str(d["primary_date"]).upper() != "NONE"]
        oldest_date = min(valid_dates) if valid_dates else None
        newest_date = max(valid_dates) if valid_dates else None
        ts_years, ts_str = _format_arabic_timespan(oldest_date, newest_date)

        from src.routing.config import FOLDER_PREFIXES
        cat_counts = {}
        total_pages = 0
        for d in docs:
            cat_raw = d["category"] or "غير مصنف"
            prefix = FOLDER_PREFIXES.get(cat_raw, "")
            cat_numbered = f"{prefix} - {cat_raw}" if (prefix and not re.match(r'^\d+\s*-\s*', cat_raw)) else cat_raw
            cat_counts[cat_numbered] = cat_counts.get(cat_numbered, 0) + 1
            total_pages += (d["page_count"] or 1)

        cat_items = [
            CategoryBreakdownItem(category=c, document_count=cnt)
            for c, cnt in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        archive = HouseArchiveProfile(
            total_documents=len(docs),
            total_pages=total_pages if total_pages > 0 else sum(b["page_count"] for b in batches),
            batch_count=len(batches),
            oldest_date=oldest_date,
            newest_date=newest_date,
            timespan_years=ts_years,
            timespan_str_ar=ts_str,
            categories=cat_items,
        )

        return HouseProfileResponse(
            house_id=house_id,
            area_id=area_id,
            tenants=tenant_profiles,
            archive=archive,
        )

    # Legacy filesystem/JSON fallback
    config = getattr(request.app.state, "config", None)
    if not config or not hasattr(config, "areas_root_path"):
        raise HTTPException(status_code=404, detail="House not found.")

    areas_root = Path(config.areas_root_path)
    state_path = areas_root / area_id / house_id / ".source_files" / f"{house_num}_state.json"
    if not state_path.exists():
        state_path = areas_root / area_id / house_id / ".source_files" / f"{house_id}_state.json"

    if not state_path.exists():
        return HouseProfileResponse(
            house_id=house_id,
            area_id=area_id,
            tenants=[],
            archive=HouseArchiveProfile(),
        )

    with open(state_path, "r", encoding="utf-8") as f:
        state_data = json.load(f)

    known_tenants = state_data.get("known_tenants", [])
    documents = state_data.get("documents", [])
    
    tenant_profiles = []
    tenant_doc_counts = {}
    for d in documents:
        pt = d.get("primary_tenant")
        if pt:
            tenant_doc_counts[pt] = tenant_doc_counts.get(pt, 0) + 1

    for idx, t in enumerate(known_tenants, 1):
        s_date = t.get("start_date") or "2020-01-01"
        e_date = t.get("end_date")
        is_active = (e_date is None or e_date == "PRESENT" or e_date == "")
        actual_e_date = None if is_active else str(e_date)
        y_int, dur_str = _format_arabic_duration(str(s_date), actual_e_date)
        t_name = t.get("name", f"Tenant {idx}")
        tenant_profiles.append(HouseTenantProfile(
            id=idx,
            name=t_name,
            start_date=str(s_date),
            end_date=actual_e_date,
            is_active=is_active,
            duration_str_ar=dur_str,
            document_count=tenant_doc_counts.get(t_name, 0),
            category_count=0,
        ))

    tenant_profiles.sort(key=lambda x: (not x.is_active, x.start_date), reverse=False)

    valid_dates = []
    cat_counts = {}
    total_pages = 0
    for d in documents:
        for dt in d.get("dates", []):
            if dt and dt != "NONE":
                valid_dates.append(dt)
        cat = d.get("category") or d.get("folder_path") or "غير مصنف"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        total_pages += len(d.get("pages", [1]))

    oldest_date = min(valid_dates) if valid_dates else None
    newest_date = max(valid_dates) if valid_dates else None
    ts_years, ts_str = _format_arabic_timespan(oldest_date, newest_date)

    cat_items = [
        CategoryBreakdownItem(category=c, document_count=cnt)
        for c, cnt in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    archive = HouseArchiveProfile(
        total_documents=len(documents),
        total_pages=total_pages,
        batch_count=1,
        oldest_date=oldest_date,
        newest_date=newest_date,
        timespan_years=ts_years,
        timespan_str_ar=ts_str,
        categories=cat_items,
    )

    return HouseProfileResponse(
        house_id=house_id,
        area_id=area_id,
        tenants=tenant_profiles,
        archive=archive,
    )


def _format_category_with_prefix(raw_category: Optional[str]) -> str:
    from src.routing.config import FOLDER_PREFIXES
    if not raw_category or not raw_category.strip():
        return "13 - رسائل متنوعة"
    trimmed = raw_category.strip()
    m = re.match(r'^(\d+)\s*-\s*(.+)$', trimmed)
    if m:
        num = int(m.group(1))
        name = m.group(2).strip()
        if name in FOLDER_PREFIXES:
            return f"{FOLDER_PREFIXES[name]} - {name}"
        return f"{num:02d} - {name}"
    if trimmed in FOLDER_PREFIXES:
        return f"{FOLDER_PREFIXES[trimmed]} - {trimmed}"
    return trimmed


@router.get("/api/areas/{area_id}/houses/{house_id}/export-zip")
async def export_house_archive_zip(request: Request, area_id: str, house_id: str, tenant_id: Optional[int] = None):
    repo = get_db_repo(request)
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not initialized.")

    conn = repo.conn
    h_cur = conn.execute("SELECT id FROM houses WHERE id = ? OR id = ?", (house_id, house_num))
    h_row = h_cur.fetchone()
    if not h_row:
        raise HTTPException(status_code=404, detail="House not found.")
    db_house_id = h_row["id"]

    docs = repo.list_documents_by_house(db_house_id)
    tenant_obj = None
    if tenant_id is not None:
        docs = [d for d in docs if d.tenant_id == tenant_id]
        tenant_obj = repo.get_tenant(tenant_id)

    config = getattr(request.app.state, "config", None)
    areas_root = Path(config.areas_root_path) if (config and hasattr(config, "areas_root_path")) else Path(".")
    house_dir = areas_root / area_id / db_house_id
    vault_dir = house_dir / "vault"

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        seen_names = set()
        for doc in docs:
            src_candidates = [
                vault_dir / f"doc_{doc.vault_id}.pdf",
                vault_dir / f"{doc.vault_id}.pdf",
                house_dir / ".source_files" / "vault" / f"doc_{doc.vault_id}.pdf",
                house_dir / ".source_files" / "vault" / f"{doc.vault_id}.pdf",
            ]
            pdf_path = next((p for p in src_candidates if p.exists() and p.is_file()), None)
            if not pdf_path:
                continue

            cat_numbered = _format_category_with_prefix(doc.category)
            category_clean = re.sub(r'[\\/*?:"<>|]', '_', cat_numbered).strip()
            title_clean = re.sub(r'[\\/*?:"<>|]', '_', doc.arabic_title or doc.vault_id).strip()
            date_prefix = f"{doc.primary_date}_" if doc.primary_date else ""
            base_filename = f"{date_prefix}{title_clean}.pdf"

            archive_path = f"{category_clean}/{base_filename}"
            counter = 1
            while archive_path in seen_names:
                archive_path = f"{category_clean}/{date_prefix}{title_clean}_{counter}.pdf"
                counter += 1
            seen_names.add(archive_path)

            zip_file.write(str(pdf_path), arcname=archive_path)

        if not seen_names:
            zip_file.writestr("README.txt", f"No documents found in vault for Area {area_id}, House {house_id}.\n")

    zip_buffer.seek(0)
    safe_area = re.sub(r'[^\w\-]', '_', area_id)
    safe_house = re.sub(r'[^\w\-]', '_', house_id)
    safe_ascii_area = safe_area.encode("ascii", "ignore").decode("ascii") or "area"
    safe_ascii_house = safe_house.encode("ascii", "ignore").decode("ascii") or "house"
    if tenant_id is not None:
        if tenant_obj and tenant_obj.name:
            safe_tenant = re.sub(r'[^\w\-]', '_', tenant_obj.name)
            filename = f"archive_{safe_area}_{safe_house}_{safe_tenant}.zip"
        else:
            filename = f"archive_{safe_area}_{safe_house}_tenant_{tenant_id}.zip"
        ascii_filename = f"archive_{safe_ascii_area}_{safe_ascii_house}_tenant_{tenant_id}.zip"
    else:
        filename = f"archive_{safe_area}_{safe_house}.zip"
        ascii_filename = f"archive_{safe_ascii_area}_{safe_ascii_house}.zip"
    quoted_filename = urllib.parse.quote(filename)

    headers = {
        "Content-Disposition": f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{quoted_filename}",
        "Content-Type": "application/zip",
    }
    return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)


def _find_system_font() -> Optional[str]:
    candidate_fonts = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    ]
    for candidate in candidate_fonts:
        if os.path.isfile(candidate):
            return candidate
    return None


def _get_text_width(text: str, fontsize: float = 7.5, fontfile: Optional[str] = None) -> float:
    if not text:
        return 0.0
    try:
        if any('\u0600' <= ch <= '\u06ff' for ch in text):
            text = get_display(arabic_reshaper.reshape(text))
    except Exception:
        pass
    if fontfile and os.path.isfile(fontfile):
        try:
            return fitz.Font(fontfile=fontfile).text_length(text, fontsize=fontsize)
        except Exception:
            pass
    try:
        return fitz.get_text_length(text, fontname="helv", fontsize=fontsize)
    except Exception:
        return len(text) * (fontsize * 0.5)


@router.get("/api/areas/{area_id}/houses/{house_id}/export-pdf")
async def export_house_archive_pdf(request: Request, area_id: str, house_id: str, tenant_id: Optional[int] = None):
    repo = get_db_repo(request)
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not initialized.")

    conn = repo.conn
    h_cur = conn.execute("SELECT id FROM houses WHERE id = ? OR id = ?", (house_id, house_num))
    h_row = h_cur.fetchone()
    if not h_row:
        raise HTTPException(status_code=404, detail="House not found.")
    db_house_id = h_row["id"]

    docs = repo.list_documents_by_house(db_house_id)
    tenant_obj = None
    if tenant_id is not None:
        docs = [d for d in docs if d.tenant_id == tenant_id]
        tenant_obj = repo.get_tenant(tenant_id)

    # Descending chronological sort: newest/most recent dates first, empty/null dates last, tie-break by vault_id
    docs_sorted = sorted(
        docs,
        key=lambda d: (
            (1, str(d.primary_date)) if d.primary_date else (0, ""),
            d.vault_id
        ),
        reverse=True
    )

    config = getattr(request.app.state, "config", None)
    areas_root = Path(config.areas_root_path) if (config and hasattr(config, "areas_root_path")) else Path(".")
    house_dir = areas_root / area_id / db_house_id
    vault_dir = house_dir / "vault"

    merged = fitz.open()
    overall_page_idx = 0
    system_font = _find_system_font()

    for doc in docs_sorted:
        src_candidates = [
            vault_dir / f"doc_{doc.vault_id}.pdf",
            vault_dir / f"{doc.vault_id}.pdf",
            house_dir / ".source_files" / "vault" / f"doc_{doc.vault_id}.pdf",
            house_dir / ".source_files" / "vault" / f"{doc.vault_id}.pdf",
        ]
        pdf_path = next((p for p in src_candidates if p.exists() and p.is_file()), None)
        if not pdf_path:
            continue
        try:
            with fitz.open(str(pdf_path)) as src:
                doc_page_count = len(src)
                cat_name = (doc.category or '').strip()
                date_str = str(doc.primary_date) if doc.primary_date else ""
                start_page_idx = len(merged)
                merged.insert_pdf(src)

                for i in range(doc_page_count):
                    overall_page_idx += 1
                    page_num = i + 1
                    page = merged[start_page_idx + i]

                    # Bottom Left: filing date (e.g. 2024-05-15). If undated, leave blank.
                    if date_str:
                        left_pt = fitz.Point(36, page.rect.height - 16)
                        page.insert_text(left_pt, date_str, fontsize=7.5, color=(0.4, 0.4, 0.45), fontname="helv")

                    # Bottom Center: category name (preserves number prefix e.g. 05 - عقود)
                    if cat_name:
                        # Contextually shape Arabic characters into connected cursive forms and apply BiDi visual reordering
                        try:
                            reshaped = arabic_reshaper.reshape(cat_name)
                            shaped_cat = get_display(reshaped)
                        except Exception:
                            shaped_cat = cat_name

                        approx_width = _get_text_width(shaped_cat, fontsize=7.5, fontfile=system_font)
                        center_pt = fitz.Point(page.rect.width / 2.0 - approx_width / 2.0, page.rect.height - 16)
                        inserted = False
                        if system_font:
                            try:
                                page.insert_text(center_pt, shaped_cat, fontsize=7.5, color=(0.4, 0.4, 0.45), fontname="f0", fontfile=system_font)
                                inserted = True
                            except Exception:
                                pass
                        if not inserted:
                            try:
                                page.insert_text(center_pt, shaped_cat, fontsize=7.5, color=(0.4, 0.4, 0.45), fontname="helv")
                            except Exception:
                                page.insert_text(center_pt, shaped_cat, fontsize=7.5, color=(0.4, 0.4, 0.45))

                    # Bottom Right: X/Y  (Z)
                    pagination_str = f"{page_num}/{doc_page_count}  ({overall_page_idx})"
                    right_width = _get_text_width(pagination_str, fontsize=7.5)
                    right_pt = fitz.Point(page.rect.width - 36 - right_width, page.rect.height - 16)
                    page.insert_text(right_pt, pagination_str, fontsize=7.5, color=(0.4, 0.4, 0.45), fontname="helv")
        except Exception:
            pass

    if len(merged) == 0:
        page = merged.new_page()
        text = f"No documents found in archive for Area {area_id}, House {house_id}."
        page.insert_text((50, 100), text, fontsize=14)

    pdf_bytes = merged.tobytes()
    merged.close()
    pdf_buffer = io.BytesIO(pdf_bytes)

    safe_area = re.sub(r'[^\w\-]', '_', area_id)
    safe_house = re.sub(r'[^\w\-]', '_', house_id)
    safe_ascii_area = safe_area.encode("ascii", "ignore").decode("ascii") or "area"
    safe_ascii_house = safe_house.encode("ascii", "ignore").decode("ascii") or "house"
    if tenant_id is not None:
        if tenant_obj and tenant_obj.name:
            safe_tenant = re.sub(r'[^\w\-]', '_', tenant_obj.name)
            filename = f"archive_{safe_area}_{safe_house}_{safe_tenant}.pdf"
        else:
            filename = f"archive_{safe_area}_{safe_house}_tenant_{tenant_id}.pdf"
        ascii_filename = f"archive_{safe_ascii_area}_{safe_ascii_house}_tenant_{tenant_id}.pdf"
    else:
        filename = f"archive_{safe_area}_{safe_house}.pdf"
        ascii_filename = f"archive_{safe_ascii_area}_{safe_ascii_house}.pdf"
    quoted_filename = urllib.parse.quote(filename)

    headers = {
        "Content-Disposition": f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{quoted_filename}",
        "Content-Type": "application/pdf",
    }
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)


@router.get("/api/areas/{area_id}/houses/{house_id}/tenants", response_model=list[TenantItem])
async def list_house_tenants(request: Request, area_id: str, house_id: str):
    repo = get_db_repo(request)
    if not repo:
        return []
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    h_cur = repo.conn.execute("SELECT id FROM houses WHERE id = ? OR id = ?", (house_id, house_num))
    h_row = h_cur.fetchone()
    if not h_row:
        raise HTTPException(status_code=404, detail="House not found.")
    db_house_id = h_row["id"]

    tenants = repo.list_tenants_by_house(db_house_id)
    seen_ids = set()
    seen_names = set()
    unique_tenants = []
    for t in tenants:
        norm_name = " ".join((t.name or "").strip().split()).lower()
        if t.id is not None and t.id in seen_ids:
            continue
        if norm_name and norm_name in seen_names:
            continue
        if t.id is not None:
            seen_ids.add(t.id)
        if norm_name:
            seen_names.add(norm_name)
        unique_tenants.append(
            TenantItem(
                id=t.id,
                name=t.name,
                start_date=str(t.start_date),
                end_date=str(t.end_date) if t.end_date else None,
                house_id=t.house_id,
            )
        )
    return unique_tenants

@router.post("/api/areas/{area_id}/houses/{house_id}/tenants", response_model=TenantReallocationResponse)
async def bulk_update_tenants(request: Request, area_id: str, house_id: str, payload: TenantBulkUpdateRequest):
    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    h_cur = repo.conn.execute("SELECT id FROM houses WHERE id = ? OR id = ?", (house_id, house_num))
    h_row = h_cur.fetchone()
    if not h_row:
        raise HTTPException(status_code=404, detail="House not found.")
    db_house_id = h_row["id"]

    current_tenants = repo.list_tenants_by_house(db_house_id)
    current_by_id = {t.id: t for t in current_tenants if t.id is not None}
    payload_ids = {t.id for t in payload.tenants if t.id is not None}

    # 1. Delete tenants that were removed in payload
    for cid in list(current_by_id.keys()):
        if cid not in payload_ids:
            repo.delete_tenant(cid)

    # 2. Update existing or insert new tenants
    for t in payload.tenants:
        s_date = str(t.start_date)[:10] if t.start_date else "1970-01-01"
        e_date = str(t.end_date)[:10] if t.end_date and str(t.end_date).strip().lower() not in ("none", "null", "present", "") else None
        if t.id and t.id in current_by_id:
            repo.update_tenant(tenant_id=t.id, name=t.name.strip(), start_date=s_date, end_date=e_date)
        else:
            repo.add_tenant(house_id=db_house_id, name=t.name.strip(), start_date=s_date, end_date=e_date)

    # 3. Automatic reallocation if requested
    reallocated_count = 0
    if payload.reallocate:
        res = repo.reallocate_house_documents(db_house_id)
        reallocated_count = res.get("reallocated_count", 0)

    clear_tree_cache()

    all_tenants = repo.list_tenants_by_house(db_house_id)
    doc_row = repo.conn.execute("SELECT COUNT(*) as cnt FROM documents WHERE house_id = ?", (db_house_id,)).fetchone()
    doc_count = doc_row["cnt"] if doc_row else 0

    return TenantReallocationResponse(
        status="success",
        reallocated_count=reallocated_count,
        total_documents=doc_count,
        tenants_count=len(all_tenants)
    )

@router.post("/api/areas/{area_id}/houses/{house_id}/reallocate", response_model=TenantReallocationResponse)
async def trigger_reallocate(request: Request, area_id: str, house_id: str):
    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    h_cur = repo.conn.execute("SELECT id FROM houses WHERE id = ? OR id = ?", (house_id, house_num))
    h_row = h_cur.fetchone()
    if not h_row:
        raise HTTPException(status_code=404, detail="House not found.")
    db_house_id = h_row["id"]

    res = repo.reallocate_house_documents(db_house_id)
    clear_tree_cache()
    return TenantReallocationResponse(
        status="success",
        reallocated_count=res.get("reallocated_count", 0),
        total_documents=res.get("total_documents", 0),
        tenants_count=res.get("tenants_count", 0)
    )

@router.patch("/api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/tenant")
async def reassign_single_document_tenant(request: Request, area_id: str, house_id: str, vault_id: str, payload: DocumentTenantUpdateRequest):
    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")
    doc = repo.get_document(vault_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    tenant = repo.get_tenant(payload.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    repo.conn.execute("UPDATE documents SET tenant_id = ?, is_manual = 1 WHERE vault_id = ?", (payload.tenant_id, vault_id))
    repo.conn.execute("UPDATE pages SET tenant_id = ? WHERE vault_id = ?", (payload.tenant_id, vault_id))
    repo.conn.commit()
    clear_tree_cache()
    return {"status": "success", "vault_id": vault_id, "tenant_id": payload.tenant_id, "tenant_name": tenant.name}

@router.patch("/api/areas/{area_id}/houses/{house_id}/documents/{vault_id}", response_model=DocumentActionResponse)
async def update_single_document(
    request: Request,
    area_id: str,
    house_id: str,
    vault_id: str,
    payload: DocumentUpdateRequest,
):
    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")
    doc = repo.get_document(vault_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    if doc.house_id != house_id and doc.house_id != house_num:
        raise HTTPException(status_code=400, detail="Document does not belong to the specified house.")

    target_tenant_name = None
    if payload.tenant_id is not None:
        tenant = repo.get_tenant(payload.tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found.")
        if tenant.house_id != house_id and tenant.house_id != house_num:
            raise HTTPException(status_code=400, detail="Cannot assign document to a tenant belonging to a different house.")
        target_tenant_name = tenant.name

    category_val = None
    if payload.category is not None:
        category_val = get_or_create_numbered_folder(repo.conn, doc.house_id, payload.category)

    updated = repo.update_document(
        vault_id,
        arabic_title=payload.arabic_title,
        category=category_val,
        tenant_id=payload.tenant_id,
        primary_date=payload.primary_date,
        is_manual=payload.is_manual if payload.is_manual is not None else 1,
        notes=payload.notes,
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update document.")

    if not target_tenant_name and updated.tenant_id:
        t = repo.get_tenant(updated.tenant_id)
        if t:
            target_tenant_name = t.name

    clear_tree_cache()
    return DocumentActionResponse(
        status="success",
        vault_id=updated.vault_id,
        arabic_title=updated.arabic_title,
        category=updated.category,
        tenant_id=updated.tenant_id,
        tenant_name=target_tenant_name,
        is_manual=getattr(updated, "is_manual", 1),
    )

@router.patch("/api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/notes", response_model=DocumentNotesResponse)
async def update_single_document_notes(
    request: Request,
    area_id: str,
    house_id: str,
    vault_id: str,
    payload: DocumentNotesRequest,
):
    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")
    doc = repo.get_document(vault_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    if doc.house_id != house_id and doc.house_id != house_num:
        raise HTTPException(status_code=400, detail="Document does not belong to the specified house.")

    updated = repo.update_document_notes(vault_id, payload.notes)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update document notes.")

    clear_tree_cache()
    return DocumentNotesResponse(
        status="success",
        vault_id=vault_id,
        notes=updated.notes,
    )

@router.get("/api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/metadata")
async def get_single_document_metadata(
    request: Request,
    area_id: str,
    house_id: str,
    vault_id: str,
):
    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")
    meta = repo.get_document_metadata(vault_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found.")

    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    if meta.get("house_id") != house_id and meta.get("house_id") != house_num:
        raise HTTPException(status_code=400, detail="Document does not belong to the specified house.")

    return meta

@router.post("/api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/copy", response_model=DocumentActionResponse)
async def copy_single_document(
    request: Request,
    area_id: str,
    house_id: str,
    vault_id: str,
    payload: DocumentCopyRequest,
):
    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")
    src_doc = repo.get_document(vault_id)
    if not src_doc:
        raise HTTPException(status_code=404, detail="Source document not found.")

    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    if src_doc.house_id != house_id and src_doc.house_id != house_num:
        raise HTTPException(status_code=400, detail="Source document does not belong to specified house.")

    target_tenant_name = None
    if payload.target_tenant_id is not None:
        tenant = repo.get_tenant(payload.target_tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Target tenant not found.")
        if tenant.house_id != house_id and tenant.house_id != house_num:
            raise HTTPException(status_code=400, detail="Cannot copy document to a tenant outside this house.")
        target_tenant_name = tenant.name

    target_cat = None
    if payload.target_category is not None:
        target_cat = get_or_create_numbered_folder(repo.conn, src_doc.house_id, payload.target_category)

    new_vault_id = uuid.uuid4().hex

    # Physical file duplicate on disk
    config = getattr(request.app.state, "config", None)
    areas_root = Path(config.areas_root_path) if (config and hasattr(config, "areas_root_path")) else Path(".")
    house_dir = areas_root / area_id / house_id
    vault_dir = house_dir / "vault"
    try:
        vault_dir.mkdir(parents=True, exist_ok=True)
        src_candidates = [
            vault_dir / f"doc_{vault_id}.pdf",
            vault_dir / f"{vault_id}.pdf",
            house_dir / ".source_files" / "vault" / f"doc_{vault_id}.pdf",
            house_dir / ".source_files" / "vault" / f"{vault_id}.pdf",
        ]
        for cand in src_candidates:
            if cand.exists() and cand.is_file():
                shutil.copy2(str(cand), str(vault_dir / f"doc_{new_vault_id}.pdf"))
                break
    except Exception:
        pass

    new_doc = repo.copy_document(
        vault_id,
        new_vault_id=new_vault_id,
        target_category=target_cat,
        target_tenant_id=payload.target_tenant_id,
        target_title=payload.target_title,
    )
    if not new_doc:
        raise HTTPException(status_code=500, detail="Failed to copy document record.")

    if not target_tenant_name and new_doc.tenant_id:
        t = repo.get_tenant(new_doc.tenant_id)
        if t:
            target_tenant_name = t.name

    clear_tree_cache()
    return DocumentActionResponse(
        status="success",
        vault_id=new_doc.vault_id,
        arabic_title=new_doc.arabic_title,
        category=new_doc.category,
        tenant_id=new_doc.tenant_id,
        tenant_name=target_tenant_name,
        is_manual=1,
    )

@router.post("/api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/reset-lock", response_model=DocumentActionResponse)
async def reset_document_lock(
    request: Request,
    area_id: str,
    house_id: str,
    vault_id: str,
):
    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")
    doc = repo.get_document(vault_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    repo.reset_document_manual_lock(vault_id)
    repo.reallocate_house_documents(doc.house_id)
    updated_doc = repo.get_document(vault_id) or doc

    target_tenant_name = None
    if updated_doc.tenant_id:
        t = repo.get_tenant(updated_doc.tenant_id)
        if t:
            target_tenant_name = t.name

    clear_tree_cache()
    return DocumentActionResponse(
        status="success",
        vault_id=vault_id,
        arabic_title=updated_doc.arabic_title,
        category=updated_doc.category,
        tenant_id=updated_doc.tenant_id,
        tenant_name=target_tenant_name,
        is_manual=0,
    )

@router.delete("/api/areas/{area_id}/houses/{house_id}/documents/{vault_id}")
async def delete_single_document(
    request: Request,
    area_id: str,
    house_id: str,
    vault_id: str,
):
    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")

    config = getattr(request.app.state, "config", None)
    areas_root = Path(config.areas_root_path) if (config and hasattr(config, "areas_root_path")) else Path(".")

    deleted = repo.delete_document(vault_id, house_id, area_id, areas_root)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    clear_tree_cache()
    return {"status": "success", "message": f"Document {vault_id} deleted"}


@router.post("/api/areas/{area_id}/houses/{house_id}/documents/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_documents(
    request: Request,
    area_id: str,
    house_id: str,
    payload: BatchDeleteRequest,
):
    if not payload.vault_ids:
        raise HTTPException(status_code=400, detail="vault_ids must not be empty.")
    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")

    config = getattr(request.app.state, "config", None)
    areas_root = Path(config.areas_root_path) if (config and hasattr(config, "areas_root_path")) else Path(".")

    deleted_ids = []
    for vid in payload.vault_ids:
        deleted = repo.delete_document(vid, house_id, area_id, areas_root)
        if deleted:
            deleted_ids.append(vid)

    clear_tree_cache()
    return BatchDeleteResponse(
        status="success",
        deleted_count=len(deleted_ids),
        vault_ids=deleted_ids,
    )


@router.post("/api/areas/{area_id}/houses/{house_id}/documents/batch-move", response_model=BatchMoveResponse)
async def batch_move_documents(
    request: Request,
    area_id: str,
    house_id: str,
    payload: BatchMoveRequest,
):
    if not payload.vault_ids:
        raise HTTPException(status_code=400, detail="vault_ids must not be empty.")
    if not payload.target_category or not payload.target_category.strip():
        raise HTTPException(status_code=400, detail="target_category must not be empty.")

    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")

    target_folder = get_or_create_numbered_folder(repo.conn, house_id, payload.target_category)

    moved_ids = []
    for vid in payload.vault_ids:
        if payload.target_tenant_id is not None:
            cur = repo.conn.execute(
                "UPDATE documents SET category = ?, tenant_id = ?, is_manual = 1 WHERE vault_id = ?",
                (target_folder, payload.target_tenant_id, vid),
            )
        else:
            cur = repo.conn.execute(
                "UPDATE documents SET category = ?, is_manual = 1 WHERE vault_id = ?",
                (target_folder, vid),
            )
        if cur.rowcount > 0:
            moved_ids.append(vid)

    if repo.autocommit:
        repo.conn.commit()

    clear_tree_cache()
    return BatchMoveResponse(
        status="success",
        moved_count=len(moved_ids),
        target_category=target_folder,
        vault_ids=moved_ids,
    )


@router.post("/api/areas/{area_id}/houses/{house_id}/documents/batch-copy", response_model=BatchCopyResponse)
async def batch_copy_documents_route(
    request: Request,
    area_id: str,
    house_id: str,
    payload: BatchCopyRequest,
):
    if not payload.vault_ids:
        raise HTTPException(status_code=400, detail="vault_ids must not be empty.")
    if not payload.target_category or not payload.target_category.strip():
        raise HTTPException(status_code=400, detail="target_category must not be empty.")

    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")

    config = getattr(request.app.state, "config", None)
    areas_root = Path(config.areas_root_path) if (config and hasattr(config, "areas_root_path")) else Path(".")

    copied_docs = repo.batch_copy_documents(
        area_id=area_id,
        house_id=house_id,
        vault_ids=payload.vault_ids,
        target_category=payload.target_category,
        target_tenant_id=payload.target_tenant_id,
        areas_root=areas_root,
    )

    clear_tree_cache()

    target_category_formatted = copied_docs[0].category if copied_docs else get_or_create_numbered_folder(repo.conn, house_id, payload.target_category)

    return BatchCopyResponse(
        status="success",
        copied_count=len(copied_docs),
        target_category=target_category_formatted,
        new_vault_ids=[d.vault_id for d in copied_docs],
    )


@router.get("/api/areas/{area_id}/houses/{house_id}/categories", response_model=list[CategoryResponse])
async def list_categories(request: Request, area_id: str, house_id: str):
    from src.routing.config import FOLDER_PREFIXES
    repo = get_db_repo(request)
    if repo:
        conn = repo.conn
        house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
        cursor = conn.execute("""
            SELECT d.vault_id, d.primary_date, d.arabic_title, d.category, d.page_count, d.is_manual, d.tenant_id, d.notes,
                   t.name as tenant_name, b.filename as batch_filename
            FROM documents d
            LEFT JOIN tenants t ON d.tenant_id = t.id
            LEFT JOIN batches b ON d.batch_id = b.id
            WHERE d.house_id = ? OR d.house_id = ?
            ORDER BY d.category ASC, d.primary_date DESC
        """, (house_id, house_num))
        rows = cursor.fetchall()
        if rows:
            categories: dict[tuple[str, str], list[VaultFileResponse]] = {}
            for r in rows:
                tenant = r["tenant_name"] or ""
                cat_raw = r["category"] or ""
                prefix = FOLDER_PREFIXES.get(cat_raw, "")
                cat_numbered = f"{prefix} - {cat_raw}" if (prefix and not re.match(r'^\d+\s*-\s*', cat_raw)) else cat_raw
                key = (tenant, cat_numbered)
                if key not in categories:
                    categories[key] = []
                categories[key].append(VaultFileResponse(
                    vault_id=r["vault_id"],
                    filename=r["batch_filename"] or f"doc_{r['vault_id']}.pdf",
                    start_page=1,
                    end_page=r["page_count"] or 1,
                    date=str(r["primary_date"]) if r["primary_date"] else "",
                    tenant=tenant,
                    tenant_id=r["tenant_id"],
                    category=cat_numbered,
                    brief_arabic_title=r["arabic_title"] or "",
                    is_manual=int(r["is_manual"] or 0),
                    notes=r["notes"]
                ))
            return [
                CategoryResponse(
                    tenant=t,
                    name=c,
                    document_count=len(docs),
                    documents=docs
                )
                for (t, c), docs in categories.items()
            ]
        h_cur = conn.execute("SELECT id FROM houses WHERE id = ? OR id = ?", (house_id, house_num))
        if h_cur.fetchone():
            return []

    config = getattr(request.app.state, "config", None)
    if not config or not hasattr(config, "areas_root_path"):
        return []
    areas_root = Path(config.areas_root_path)
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    state_path = areas_root / area_id / house_id / ".source_files" / f"{house_num}_state.json"

    from src.routing.config import FOLDER_PREFIXES
    
    categories: dict[tuple[str, str], list[VaultFileResponse]] = {}
    
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state_data = json.load(f)
        except Exception:
            raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

        for group in _get_document_groups(state_data):
            tenant = group.get("primary_tenant")
            cat_raw = group.get("folder_path") or group.get("category")
            if tenant and cat_raw:
                prefix = FOLDER_PREFIXES.get(cat_raw, "")
                cat_numbered = f"{prefix} - {cat_raw}" if prefix else cat_raw
                key = (tenant, cat_numbered)
                
                if key not in categories:
                    categories[key] = []
                
                doc = VaultFileResponse(
                    vault_id=group.get("vault_id", ""),
                    filename=group.get("filename", ""),
                    start_page=group.get("start_page", 1),
                    end_page=group.get("end_page", 1),
                    date=group.get("dates", [""])[0] if group.get("dates") else "",
                    tenant=tenant,
                    brief_arabic_title=group.get("brief_arabic_title", "")
                )
                categories[key].append(doc)
    else:
        house_entry = areas_root / area_id / house_id
        if house_entry.exists():
            for tenant_dir in house_entry.iterdir():
                if tenant_dir.is_dir() and tenant_dir.name != ".source_files":
                    m = re.match(r'^(.*?)\s*‎?\((.*?)\)‎?$', tenant_dir.name)
                    t_name = m.group(1).strip() if m else tenant_dir.name
                    for cat_dir in tenant_dir.iterdir():
                        if cat_dir.is_dir():
                            cat_raw = cat_dir.name
                            key = (t_name, cat_raw)
                            if key not in categories:
                                categories[key] = []
                            for doc_file in cat_dir.glob("*.pdf"):
                                doc_m = re.match(r'^(\d{4}-\d{2}-\d{2})\s*-\s*(.*?)\.pdf$', doc_file.name)
                                date_str = doc_m.group(1) if doc_m else ""
                                title = doc_m.group(2) if doc_m else doc_file.stem
                                rel_path = str(doc_file.relative_to(house_entry))
                                encoded = base64.urlsafe_b64encode(rel_path.encode('utf-8')).decode('utf-8').rstrip("=")
                                doc = VaultFileResponse(
                                    vault_id=f"fs_{encoded}",
                                    filename=doc_file.name,
                                    start_page=1,
                                    end_page=1,
                                    date=date_str,
                                    tenant=t_name,
                                    brief_arabic_title=title
                                )
                                categories[key].append(doc)

    return [
        CategoryResponse(
            tenant=t,
            name=c,
            document_count=len(docs),
            documents=docs
        )
        for (t, c), docs in categories.items()
    ]

@router.delete("/api/areas/{area_id}/houses/{house_id}/categories/{category_name}")
async def delete_custom_category(request: Request, area_id: str, house_id: str, category_name: str):
    from src.routing.config import FOLDER_PREFIXES
    clean_name = category_name.strip()
    is_standard = (
        clean_name in FOLDER_PREFIXES
        or any(clean_name == f"{prefix} - {cat}" for cat, prefix in FOLDER_PREFIXES.items())
        or any(clean_name.endswith(cat) for cat in FOLDER_PREFIXES)
    )
    if is_standard:
        raise HTTPException(status_code=400, detail="Cannot delete a standard category folder.")

    repo = get_db_repo(request)
    if not repo:
        raise HTTPException(status_code=500, detail="Database repository not available.")

    conn = repo.conn
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    default_target = "13 - رسائل متنوعة"

    # Reassign any documents in this custom category for this house to '13 - رسائل متنوعة'
    cursor = conn.execute("""
        UPDATE documents
        SET category = ?
        WHERE (house_id = ? OR house_id = ?) AND (category = ? OR category LIKE ?)
    """, (default_target, house_id, house_num, clean_name, f"%{clean_name}%"))
    conn.commit()

    clear_tree_cache()
    return {"status": "success", "deleted_category": clean_name, "reassigned_docs": cursor.rowcount}

@router.get("/api/areas/{area_id}/houses/{house_id}/pdf/{vault_id}")
async def get_pdf(request: Request, area_id: str, house_id: str, vault_id: str):
    validate_id(vault_id, r"^[a-zA-Z0-9_-]+$")
    config = getattr(request.app.state, "config", None)
    areas_root = Path(config.areas_root_path) if (config and hasattr(config, "areas_root_path")) else Path(".")
    house_dir = areas_root / area_id / house_id

    pdf_path = None
    if vault_id.startswith("fs_"):
        try:
            b64_str = vault_id[3:]
            b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
            rel_path = base64.urlsafe_b64decode(b64_str).decode('utf-8')
            pdf_path = house_dir / rel_path
        except Exception:
            raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    else:
        # Check modern DB vault path first, then legacy .source_files/vault
        candidates = [
            house_dir / "vault" / f"doc_{vault_id}.pdf",
            house_dir / "vault" / f"{vault_id}.pdf",
            house_dir / ".source_files" / "vault" / f"doc_{vault_id}.pdf",
            house_dir / ".source_files" / "vault" / f"{vault_id}.pdf",
        ]
        repo = get_db_repo(request)
        if repo:
            cur = repo.conn.execute("""
                SELECT b.file_path, b.filename FROM documents d
                JOIN batches b ON d.batch_id = b.id
                WHERE d.vault_id = ?
            """, (vault_id,))
            b_row = cur.fetchone()
            if b_row and b_row["file_path"]:
                candidates.append(Path(b_row["file_path"]))

        for cand in candidates:
            if cand.exists() and cand.is_file():
                pdf_path = cand
                break

    if not pdf_path or not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return FileResponse(pdf_path, media_type="application/pdf")

def _house_sort_key(entry: Path) -> tuple[int, str]:
    match = re.search(r'(\d+)', entry.name)
    num = int(match.group(1)) if match else 999999999
    return (num, entry.name)

_TREE_CACHE = None
_TREE_CACHE_TIME = 0
_TREE_CACHE_PATH = None
TREE_CACHE_TTL = 300  # 5 minutes

def clear_tree_cache():
    global _TREE_CACHE, _TREE_CACHE_TIME, _TREE_CACHE_PATH
    _TREE_CACHE = None
    _TREE_CACHE_TIME = 0
    _TREE_CACHE_PATH = None

@router.get("/api/tree", response_model=list[TreeItemResponse])
async def get_tree(request: Request, include_categories: bool = False, include_timeline: bool = False):
    """
    Walk the database or disk structure:
        If SQLite repo is available, execute optimized queries directly.
        Otherwise walk the real 3-level disk structure.
    """
    repo = get_db_repo(request)
    if repo:
        conn = repo.conn
        cursor = conn.execute("SELECT id, code FROM areas ORDER BY id")
        areas_rows = cursor.fetchall()

        cursor = conn.execute("SELECT id, area_id FROM houses ORDER BY id")
        houses_rows = cursor.fetchall()

        cursor = conn.execute(
            "SELECT id, house_id, name, start_date, end_date FROM tenants "
            "ORDER BY (CASE WHEN end_date IS NULL OR end_date = '' OR LOWER(end_date) = 'present' THEN 1 ELSE 0 END) DESC, "
            "start_date DESC, id DESC"
        )
        tenants_rows = cursor.fetchall()

        cursor = conn.execute("SELECT house_id, category, COUNT(*) as doc_count FROM documents GROUP BY house_id, category")
        doc_rows = cursor.fetchall()

        timeline_by_house: dict[str, list[dict]] = {}
        if include_timeline:
            t_cur = conn.execute("SELECT vault_id, house_id, primary_date, arabic_title, category FROM documents ORDER BY primary_date DESC")
            for r in t_cur.fetchall():
                timeline_by_house.setdefault(r["house_id"], []).append(r)

        houses_by_area: dict[str, list[dict]] = {}
        for h in houses_rows:
            houses_by_area.setdefault(h["area_id"], []).append(h)

        tenants_by_house: dict[str, list[dict]] = {}
        for t in tenants_rows:
            tenants_by_house.setdefault(t["house_id"], []).append(t)

        cat_counts_by_house: dict[str, dict[str, int]] = {}
        total_docs_by_house: dict[str, int] = {}
        for d in doc_rows:
            h_id = d["house_id"]
            cat_raw = d["category"]
            cnt = d["doc_count"]
            total_docs_by_house[h_id] = total_docs_by_house.get(h_id, 0) + cnt
            if cat_raw:
                clean_cat = re.sub(r'^\d+\s*-\s*', '', cat_raw)
                cat_counts_by_house.setdefault(h_id, {})
                cat_counts_by_house[h_id][clean_cat] = cat_counts_by_house[h_id].get(clean_cat, 0) + cnt

        current_year = datetime.now().year
        today_str = date.today().isoformat()
        result: list[TreeItemResponse] = []

        for a in areas_rows:
            area_id = a["id"]
            area_houses = houses_by_area.get(area_id, [])
            area_houses.sort(key=lambda h: _house_sort_key_str(h["id"]))

            house_nodes: list[TreeItemResponse] = []
            for h in area_houses:
                house_id = h["id"]
                h_tenants = tenants_by_house.get(house_id, [])

                active_t = None
                for t in h_tenants:
                    end_d = t["end_date"]
                    if not end_d or str(end_d) >= today_str or str(end_d).lower() == "present":
                        active_t = t
                        break

                if not active_t and " - " in house_id:
                    cand = house_id.split(" - ", 1)[1].strip()
                    for t in h_tenants:
                        if t["name"] == cand:
                            active_t = t
                            break

                if not active_t and h_tenants:
                    active_t = h_tenants[0]

                house_duration_cat = None
                house_subtitle = None
                active_tenant_name = None

                if active_t:
                    active_tenant_name = active_t["name"]
                    s_date_str = str(active_t["start_date"]) if active_t["start_date"] else ""
                    m_year = re.search(r'(\d{4})', s_date_str)
                    if m_year:
                        start_year = int(m_year.group(1))
                        duration = current_year - start_year
                        if duration < 5:
                            house_duration_cat = "short"
                        elif duration < 10:
                            house_duration_cat = "medium"
                        else:
                            house_duration_cat = "long"
                        house_subtitle = f"Since {start_year} ({duration}y)"
                elif h_tenants:
                    latest = h_tenants[0]
                    s_str = str(latest["start_date"])[:4] if latest["start_date"] else ""
                    e_str = str(latest["end_date"])[:4] if latest["end_date"] else ""
                    if s_str and e_str and s_str != e_str:
                        house_subtitle = f"{s_str} - {e_str}"
                    elif s_str:
                        house_subtitle = f"{s_str}"

                tenant_nodes: list[TreeItemResponse] = []
                for t in h_tenants:
                    t_name = t["name"]
                    t_start = str(t["start_date"]) if t["start_date"] else ""
                    t_end = str(t["end_date"]) if t["end_date"] else ""
                    s_m = re.search(r'(\d{4})', t_start)
                    e_m = re.search(r'(\d{4})', t_end)
                    s_y = int(s_m.group(1)) if s_m else None
                    e_y = int(e_m.group(1)) if e_m else None

                    is_active = (active_t and t["id"] == active_t["id"])
                    t_dur_cat = None
                    t_sub = None

                    if s_y:
                        if is_active:
                            duration = current_year - s_y
                            if duration < 5:
                                t_dur_cat = "short"
                            elif duration < 10:
                                t_dur_cat = "medium"
                            else:
                                t_dur_cat = "long"
                            t_sub = f"{s_y} - Present"
                        elif e_y and e_y != s_y:
                            t_sub = f"{s_y} - {e_y}"
                        else:
                            t_sub = f"{s_y}"

                    tenant_nodes.append(TreeItemResponse(
                        id=f"{house_id}_{t_name}",
                        name=t_name,
                        subtitle=t_sub,
                        duration_category=t_dur_cat,
                        type="tenant"
                    ))

                h_cat_counts = cat_counts_by_house.get(house_id, {})
                h_total_docs = total_docs_by_house.get(house_id, 0)

                house_children = list(tenant_nodes)
                if include_categories:
                    for cat_name, cat_count in sorted(h_cat_counts.items()):
                        house_children.append(TreeItemResponse(
                            id=f"{house_id}_cat_{cat_name}",
                            name=cat_name,
                            subtitle=f"{cat_count} docs",
                            type="category"
                        ))
                if include_timeline and house_id in timeline_by_house:
                    for t_doc in timeline_by_house[house_id]:
                        house_children.append(TreeItemResponse(
                            id=f"{house_id}_timeline_{t_doc['vault_id']}",
                            name=t_doc["arabic_title"] or t_doc["category"] or "Doc",
                            subtitle=str(t_doc["primary_date"]) if t_doc["primary_date"] else None,
                            type="document"
                        ))

                house_nodes.append(TreeItemResponse(
                    id=house_id,
                    name=house_id,
                    type="house",
                    subtitle=house_subtitle,
                    duration_category=house_duration_cat,
                    current_tenant=active_tenant_name,
                    total_documents=h_total_docs,
                    category_counts=h_cat_counts,
                    children=house_children
                ))

            result.append(TreeItemResponse(
                id=f"area_{area_id}",
                name=area_id,
                type="area",
                children=house_nodes
            ))
        return result

    config = getattr(request.app.state, "config", None)
    if not config or not hasattr(config, "areas_root_path"):
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    areas_root = Path(config.areas_root_path)
    if not areas_root.exists():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    global _TREE_CACHE, _TREE_CACHE_TIME, _TREE_CACHE_PATH
    now = time.time()
    if (
        _TREE_CACHE is not None
        and _TREE_CACHE_PATH == str(areas_root)
        and (now - _TREE_CACHE_TIME) < TREE_CACHE_TTL
    ):
        return _TREE_CACHE

    area_mappings = config.area_mappings or {}

    areas: dict[str, TreeItemResponse] = {}

    for area_entry in sorted(areas_root.iterdir()):
        if not area_entry.is_dir() or area_entry.name.startswith("."):
            continue

        area_name = area_entry.name  # e.g. "Safra C"

        if area_name not in areas:
            areas[area_name] = TreeItemResponse(
                id=f"area_{area_name}",
                name=area_name,
                type="area",
                children=[]
            )

        # Walk house folders inside this area
        for house_entry in sorted(area_entry.iterdir(), key=_house_sort_key):
            if not house_entry.is_dir() or house_entry.name.startswith("."):
                continue

            house_dir_name = house_entry.name   # e.g. "1245 - Ali"
            house_id = house_dir_name.split(" - ")[0] if " - " in house_dir_name else house_dir_name

            house_node = TreeItemResponse(
                id=house_dir_name,
                name=house_dir_name,
                type="house",
                children=[]
            )

            report_path = house_entry / ".source_files" / f"{house_id}_report.json"
            state_path = house_entry / ".source_files" / f"{house_id}_state.json"
            tenants_with_dates: dict[str, set[int]] = {}
            tenant_is_present: dict[str, bool] = {}
            category_counts: dict[str, int] = {}
            total_docs = 0

            if report_path.exists():
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        rep_data = json.load(f)
                    doc_list = rep_data if isinstance(rep_data, list) else rep_data.get("documents", [])
                    if isinstance(doc_list, list):
                        total_docs = len(doc_list)
                        for doc in doc_list:
                            cat_raw = doc.get("folder_path") or doc.get("category")
                            if cat_raw:
                                clean_cat = re.sub(r'^\d+\s*-\s*', '', cat_raw)
                                category_counts[clean_cat] = category_counts.get(clean_cat, 0) + 1
                            tenant = doc.get("primary_tenant") or doc.get("tenant")
                            if tenant:
                                if tenant not in tenants_with_dates:
                                    tenants_with_dates[tenant] = set()
                                for d in doc.get("dates", []):
                                    if d and d != "NONE":
                                        year_match = re.search(r'(\d{4})', d)
                                        if year_match:
                                            tenants_with_dates[tenant].add(int(year_match.group(1)))
                                for sc in doc.get("shortcuts", []):
                                    if "الآن" in sc or "present" in sc.lower():
                                        tenant_is_present[tenant] = True
                except Exception:
                    pass

            if not tenants_with_dates and state_path.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                    
                    manifest = state_data.get("manifest") or {}
                    per_page = manifest.get("per_page", [])
                    for doc in per_page:
                        tenant = doc.get("tenant")
                        if tenant:
                            tf = doc.get("target_folder", "")
                            if "الآن" in tf or "present" in tf.lower():
                                tenant_is_present[tenant] = True
                    
                    doc_groups = _get_document_groups(state_data)
                    if not total_docs:
                        total_docs = len(doc_groups)
                    for group in doc_groups:
                        cat_raw = group.get("folder_path") or group.get("category")
                        if cat_raw:
                            clean_cat = re.sub(r'^\d+\s*-\s*', '', cat_raw)
                            category_counts[clean_cat] = category_counts.get(clean_cat, 0) + 1
                        tenant = group.get("primary_tenant")
                        if tenant:
                            if tenant not in tenants_with_dates:
                                tenants_with_dates[tenant] = set()
                            
                            doc_dates = group.get("dates", [])
                            for d in doc_dates:
                                if d and d != "NONE":
                                    year_match = re.search(r'(\d{4})', d)
                                    if year_match:
                                        tenants_with_dates[tenant].add(int(year_match.group(1)))
                except Exception:
                    pass

            if not tenants_with_dates and house_entry.exists():
                # Fast fallback: examine directory names directly without recursive globbing
                for tenant_dir in house_entry.iterdir():
                    if tenant_dir.is_dir() and not tenant_dir.name.startswith("."):
                        m = re.match(r'^(.*?)\s*‎?\((.*?)\)‎?$', tenant_dir.name)
                        t_name = m.group(1).strip() if m else tenant_dir.name
                        if "الآن" in tenant_dir.name or "present" in tenant_dir.name.lower():
                            tenant_is_present[t_name] = True
                        if t_name not in tenants_with_dates:
                            tenants_with_dates[t_name] = set()
                        if m and m.group(2):
                            year_matches = re.findall(r'(\d{4})', m.group(2))
                            for y in year_matches:
                                tenants_with_dates[t_name].add(int(y))

            current_year = datetime.now().year

            def _tenant_sort_key(item):
                t_name, years = item
                is_pres = 1 if tenant_is_present.get(t_name) else 0
                max_year = max(years) if years else 0
                return (is_pres, max_year)

            sorted_tenants = sorted(tenants_with_dates.items(), key=_tenant_sort_key, reverse=True)
            for t, years in sorted_tenants:
                subtitle = None
                duration_category = None
                if years:
                    min_val = min(years)
                    max_val = max(years)
                    
                    if tenant_is_present.get(t):
                        # Only color-code currently active tenants
                        actual_max = current_year
                        duration = actual_max - min_val
                        if duration < 5:
                            duration_category = "short"
                        elif duration < 10:
                            duration_category = "medium"
                        else:
                            duration_category = "long"
                    # Past tenants keep duration_category = None → grey badge

                    if tenant_is_present.get(t):
                        subtitle = f"{min_val} - Present"
                    elif min_val == max_val:
                        subtitle = f"{min_val}"
                    else:
                        subtitle = f"{min_val} - {max_val}"
                house_node.children.append(TreeItemResponse(
                    id=f"{house_dir_name}_{t}",
                    name=t,
                    subtitle=subtitle,
                    duration_category=duration_category,
                    type="tenant"
                ))

            # Determine active tenant and house-level metrics for grid view
            active_tenant = None
            for t in tenants_with_dates.keys():
                if tenant_is_present.get(t):
                    active_tenant = t
                    break
            
            if not active_tenant and " - " in house_dir_name:
                cand = house_dir_name.split(" - ", 1)[1].strip()
                if cand in tenants_with_dates:
                    active_tenant = cand

            if not active_tenant and len(tenants_with_dates) == 1:
                active_tenant = next(iter(tenants_with_dates.keys()))

            house_duration_cat = None
            house_sub = None

            if active_tenant and tenants_with_dates.get(active_tenant):
                years = tenants_with_dates[active_tenant]
                min_val = min(years)
                max_val = max(years)
                is_pres = tenant_is_present.get(active_tenant, False)
                if is_pres or active_tenant == (house_dir_name.split(" - ", 1)[1].strip() if " - " in house_dir_name else ""):
                    duration = current_year - min_val
                    if duration < 5:
                        house_duration_cat = "short"
                    elif duration < 10:
                        house_duration_cat = "medium"
                    else:
                        house_duration_cat = "long"
                    house_sub = f"Since {min_val} ({duration}y)"
                elif min_val == max_val:
                    house_sub = f"{min_val}"
                else:
                    house_sub = f"{min_val} - {max_val}"

            house_node.current_tenant = active_tenant
            house_node.duration_category = house_duration_cat
            house_node.subtitle = house_sub
            house_node.total_documents = total_docs
            house_node.category_counts = category_counts

            areas[area_name].children.append(house_node)

    result = list(areas.values())
    _TREE_CACHE = result
    _TREE_CACHE_TIME = time.time()
    _TREE_CACHE_PATH = str(areas_root)
    return result

_SEARCH_CACHE = None
_SEARCH_CACHE_TIME = 0
SEARCH_CACHE_TTL = 300  # 5 minutes

def get_search_index(areas_root: Path):
    global _SEARCH_CACHE, _SEARCH_CACHE_TIME
    now = time.time()
    if _SEARCH_CACHE is not None and (now - _SEARCH_CACHE_TIME) < SEARCH_CACHE_TTL:
        return _SEARCH_CACHE

    houses = []
    tenants = []
    documents = []

    for area_entry in sorted(areas_root.iterdir()):
        if not area_entry.is_dir():
            continue

        area_name = area_entry.name

        for house_entry in sorted(area_entry.iterdir(), key=_house_sort_key):
            if not house_entry.is_dir():
                continue

            house_dir_name = house_entry.name
            house_id = house_dir_name.split(" - ")[0] if " - " in house_dir_name else house_dir_name

            houses.append({
                "house_dir_name": house_dir_name,
                "area_name": area_name
            })

            state_path = house_entry / ".source_files" / f"{house_id}_state.json"
            house_tenants: set[str] = set()
            if state_path.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state_data = json.load(f)

                    for group in _get_document_groups(state_data):
                        tenant = group.get("primary_tenant")
                        if tenant:
                            house_tenants.add(tenant)

                    for t in house_tenants:
                        tenants.append({
                            "tenant_name": t,
                            "house_dir_name": house_dir_name,
                            "area_name": area_name
                        })
                except Exception:
                    pass
            else:
                try:
                    for tenant_dir in house_entry.iterdir():
                        if tenant_dir.is_dir() and tenant_dir.name != ".source_files":
                            m = re.match(r'^(.*?)\s*‎?\((.*?)\)‎?$', tenant_dir.name)
                            t_name = m.group(1).strip() if m else tenant_dir.name
                            house_tenants.add(t_name)
                            
                            for cat_dir in tenant_dir.iterdir():
                                if cat_dir.is_dir():
                                    for doc_file in cat_dir.glob("*.pdf"):
                                        doc_m = re.match(r'^(\d{4}-\d{2}-\d{2})\s*-\s*(.*?)\.pdf$', doc_file.name)
                                        title = doc_m.group(2) if doc_m else doc_file.stem
                                        rel_path = str(doc_file.relative_to(house_entry))
                                        encoded = base64.urlsafe_b64encode(rel_path.encode('utf-8')).decode('utf-8').rstrip("=")
                                        documents.append({
                                            "content": "",
                                            "title_field": title.lower(),
                                            "vault_id": f"fs_{encoded}",
                                            "doc_title": title,
                                            "house_dir_name": house_dir_name,
                                            "area_name": area_name
                                        })
                                        
                    for t in house_tenants:
                        tenants.append({
                            "tenant_name": t,
                            "house_dir_name": house_dir_name,
                            "area_name": area_name
                        })
                except Exception:
                    pass

            report_path = house_entry / ".source_files" / f"{house_id}_report.json"
            if report_path.exists():
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_data = json.load(f)

                    for doc in report_data.get("documents", []):
                        documents.append({
                            "content": doc.get("content", "").lower(),
                            "title_field": doc.get("brief_arabic_title", "").lower(),
                            "vault_id": doc.get("vault_id", ""),
                            "doc_title": doc.get("brief_arabic_title", "Document"),
                            "house_dir_name": house_dir_name,
                            "area_name": area_name
                        })
                except Exception:
                    pass

    _SEARCH_CACHE = {
        "houses": houses,
        "tenants": tenants,
        "documents": documents
    }
    _SEARCH_CACHE_TIME = now
    return _SEARCH_CACHE

@router.get("/api/search", response_model=list[SearchResultResponse])
async def search(request: Request, q: str = ""):
    q = q.lower().strip()
    if not q:
        return []

    repo = get_db_repo(request)
    if repo:
        conn = repo.conn
        results = []

        # 1. Houses matching q
        cursor = conn.execute("""
            SELECT h.id, h.area_id, 
                   (SELECT COUNT(*) FROM documents WHERE house_id = h.id) as doc_count,
                   (SELECT name FROM tenants WHERE house_id = h.id AND (end_date IS NULL OR end_date = '' OR LOWER(end_date) = 'present') ORDER BY start_date DESC LIMIT 1) as current_tenant
            FROM houses h 
            WHERE LOWER(h.id) LIKE ? OR LOWER(h.area_id) LIKE ? 
            ORDER BY h.id
        """, (f"%{q}%", f"%{q}%"))
        for row in cursor.fetchall():
            h_id = row["id"]
            a_id = row["area_id"]
            d_cnt = row["doc_count"] or 0
            c_tenant = row["current_tenant"]
            sub_parts = [a_id]
            if c_tenant:
                sub_parts.append(c_tenant)
            sub_parts.append(f"{d_cnt} Documents")
            results.append(SearchResultResponse(
                id=h_id,
                type="house",
                title=f"House {h_id}",
                subtitle=" • ".join(sub_parts),
                url=f"/#/area/{a_id}/house/{h_id}",
                area_id=a_id,
                house_id=h_id,
                tenant_name=c_tenant,
                extra_info=f"{d_cnt} Docs"
            ))

        # 2. Tenants matching q (with phonetic, token-aware and fuzzy matching)
        cursor = conn.execute("""
            SELECT t.id, t.name as tenant_name, t.start_date, t.end_date, t.house_id, h.area_id
            FROM tenants t
            JOIN houses h ON t.house_id = h.id
            ORDER BY t.start_date DESC
        """)
        scored_tenants = []
        for t in cursor.fetchall():
            t_name = t["tenant_name"]
            score = score_tenant_match(q, t_name, str(t["house_id"]))
            if score > 0:
                s_yr = t["start_date"][:4] if t["start_date"] else ""
                e_yr = "Present" if not t["end_date"] or str(t["end_date"]).lower() == "present" else str(t["end_date"])[:4]
                tenure_str = f"{s_yr} - {e_yr}" if s_yr else ""
                sub_label = f"House {t['house_id']} ({tenure_str}) • {t['area_id']}" if tenure_str else f"House {t['house_id']} • {t['area_id']}"
                scored_tenants.append((score, SearchResultResponse(
                    id=f"{t['house_id']}_{t_name}",
                    type="tenant",
                    title=t_name,
                    subtitle=sub_label,
                    url=f"/#/area/{t['area_id']}/house/{t['house_id']}",
                    area_id=t["area_id"],
                    house_id=t["house_id"],
                    tenant_name=t_name,
                    extra_info=tenure_str
                )))

        scored_tenants.sort(key=lambda x: x[0], reverse=True)
        for _, item in scored_tenants:
            results.append(item)

        # 3. Documents matching arabic_title or category or content_explanation in pages
        cursor = conn.execute("""
            SELECT d.vault_id, d.arabic_title, d.category, d.primary_date, d.is_manual, d.house_id, h.area_id, t.name as tenant_name
            FROM documents d
            JOIN houses h ON d.house_id = h.id
            LEFT JOIN tenants t ON d.tenant_id = t.id
            WHERE d.arabic_title LIKE ?
               OR d.category LIKE ?
               OR d.notes LIKE ?
               OR EXISTS (
                   SELECT 1 FROM pages p 
                   WHERE p.vault_id = d.vault_id 
                     AND (p.content_explanation LIKE ? OR p.subject LIKE ?)
               )
            ORDER BY d.primary_date DESC
            LIMIT 50
        """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"))

        for d in cursor.fetchall():
            title = d["arabic_title"] or d["category"] or "Document"
            cat = d["category"] or "Uncategorized"
            t_name = d["tenant_name"] or "No Tenant"
            p_date = str(d["primary_date"]) if d["primary_date"] else ""
            path_str = f"{d['area_id']} › House {d['house_id']} › {t_name} › {cat}"
            results.append(SearchResultResponse(
                id=f"{d['house_id']}_doc_{d['vault_id']}",
                type="document",
                title=title,
                subtitle=path_str,
                url=f"/#/area/{d['area_id']}/house/{d['house_id']}",
                area_id=d["area_id"],
                house_id=d["house_id"],
                tenant_name=d["tenant_name"],
                category=cat,
                date=p_date,
                vault_id=d["vault_id"],
                is_manual=int(d["is_manual"] or 0)
            ))

        seen: set[str] = set()
        unique_results = []
        for r in results:
            if r.id not in seen:
                seen.add(r.id)
                unique_results.append(r)
        return unique_results[:60]

    config = getattr(request.app.state, "config", None)
    if not config or not hasattr(config, "areas_root_path"):
        return []
    areas_root = Path(config.areas_root_path)
    if not areas_root.exists():
        return []

    results = []
    
    index = get_search_index(areas_root)
    
    for h in index["houses"]:
        if q in h["house_dir_name"].lower():
            results.append(SearchResultResponse(
                id=h["house_dir_name"],
                type="house",
                title=h["house_dir_name"],
                subtitle=f"House in {h['area_name']}",
                url=f"/#/area/{h['area_name']}/house/{h['house_dir_name']}",
                area_id=h["area_name"],
                house_id=h["house_dir_name"]
            ))
            
    q_phonetic = phonetic_normalize(q)
    
    for t in index["tenants"]:
        t_name = t["tenant_name"]
        t_lower = t_name.lower()
        t_phonetic = phonetic_normalize(t_lower)
        is_match = False
        if q in t_lower:
            is_match = True
        elif q_phonetic.replace(" ", "") in t_phonetic.replace(" ", ""):
            is_match = True
        else:
            if len(q.split()) == 1:
                if difflib.get_close_matches(q, t_lower.split(), n=1, cutoff=0.7) or \
                   difflib.get_close_matches(q_phonetic, t_phonetic.split(), n=1, cutoff=0.7):
                    is_match = True
            else:
                if difflib.SequenceMatcher(None, q, t_lower).ratio() >= 0.7 or \
                   difflib.SequenceMatcher(None, q_phonetic, t_phonetic).ratio() >= 0.7:
                    is_match = True
        if is_match:
            results.append(SearchResultResponse(
                id=f"{t['house_dir_name']}_{t_name}",
                type="tenant",
                title=t_name,
                subtitle=f"Tenant in {t['house_dir_name']} • {t['area_name']}",
                url=f"/#/area/{t['area_name']}/house/{t['house_dir_name']}",
                area_id=t["area_name"],
                house_id=t["house_dir_name"],
                tenant_name=t_name
            ))

    for d in index["documents"]:
        if q in d["content"] or q in d["title_field"]:
            path_str = f"{d['area_name']} › {d['house_dir_name']}"
            results.append(SearchResultResponse(
                id=f"{d['house_dir_name']}_doc_{d['vault_id']}",
                type="document",
                title=d["doc_title"],
                subtitle=path_str,
                url=f"/#/area/{d['area_name']}/house/{d['house_dir_name']}",
                area_id=d["area_name"],
                house_id=d["house_dir_name"],
                vault_id=d["vault_id"]
            ))

    seen = set()
    unique_results = []
    for r in results:
        if r.id not in seen:
            seen.add(r.id)
            unique_results.append(r)

    return unique_results[:60]


ALLOWED_DB_TABLES = {"areas", "houses", "tenants", "batches", "pages", "documents"}


@router.get("/api/db/info")
async def get_db_info(request: Request):
    repo = get_db_repo(request)
    if not repo:
        config = getattr(request.app.state, "config", None)
        areas_root = Path(config.areas_root_path) if config and getattr(config, "areas_root_path", None) else None
        candidates = []
        if areas_root:
            candidates.extend([areas_root / "organizer.db", *areas_root.glob("*/organizer.db")])
        candidates.append(Path("organizer.db"))
        for cand in candidates:
            if cand.exists():
                from src.db.connection import get_db_connection
                conn = get_db_connection(str(cand))
                repo = Repository(conn)
                request.app.state.repo = repo
                request.app.state.db_path = str(cand)
                break

    if not repo:
        return {
            "connected": False,
            "db_path": None,
            "tables": {}
        }

    conn = repo.conn
    db_path = getattr(request.app.state, "db_path", "organizer.db")
    tables_counts = {}
    for tbl in ["areas", "houses", "tenants", "batches", "pages", "documents"]:
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {tbl}")
            tables_counts[tbl] = cursor.fetchone()[0]
        except Exception:
            tables_counts[tbl] = 0

    return {
        "connected": True,
        "db_path": str(db_path),
        "tables": tables_counts
    }


@router.get("/api/db/tables/{table_name}")
async def get_db_table_data(
    table_name: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None
):
    if table_name not in ALLOWED_DB_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table '{table_name}'. Allowed tables: {sorted(list(ALLOWED_DB_TABLES))}"
        )

    repo = get_db_repo(request)
    if not repo:
        config = getattr(request.app.state, "config", None)
        areas_root = Path(config.areas_root_path) if config and getattr(config, "areas_root_path", None) else None
        candidates = []
        if areas_root:
            candidates.extend([areas_root / "organizer.db", *areas_root.glob("*/organizer.db")])
        candidates.append(Path("organizer.db"))
        for cand in candidates:
            if cand.exists():
                from src.db.connection import get_db_connection
                conn = get_db_connection(str(cand))
                repo = Repository(conn)
                request.app.state.repo = repo
                request.app.state.db_path = str(cand)
                break

    if not repo:
        raise HTTPException(status_code=503, detail="Database not connected.")

    conn = repo.conn
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]

    where_clause = ""
    params = []
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        clauses = [f"CAST({col} AS TEXT) LIKE ?" for col in columns]
        where_clause = f" WHERE {' OR '.join(clauses)}"
        params = [search_term] * len(columns)

    count_sql = f"SELECT COUNT(*) FROM {table_name}{where_clause}"
    total = conn.execute(count_sql, params).fetchone()[0]

    data_sql = f"SELECT * FROM {table_name}{where_clause} LIMIT ? OFFSET ?"
    query_params = list(params) + [limit, offset]
    cursor = conn.execute(data_sql, query_params)
    rows = [dict(row) for row in cursor.fetchall()]

    return {
        "table": table_name,
        "columns": columns,
        "total": total,
        "limit": limit,
        "offset": offset,
        "rows": rows
    }


def get_db_path_for_ingest(request: Request) -> str:
    db_path = getattr(request.app.state, "db_path", None)
    if db_path:
        return str(db_path)
    config = getattr(request.app.state, "config", None)
    if config and getattr(config, "db_path", None):
        return str(config.db_path)
    repo = get_db_repo(request)
    if repo and repo.conn:
        try:
            cursor = repo.conn.execute("PRAGMA database_list")
            for row in cursor.fetchall():
                if row[1] == "main" and row[2]:
                    return str(row[2])
        except Exception:
            pass
    areas_root = get_areas_root_for_ingest(request)
    candidates = [
        areas_root / "organizer.db",
        *areas_root.glob("*/organizer.db"),
        Path("organizer.db"),
        Path("file_organizer.db"),
    ]
    for cand in candidates:
        if cand.exists():
            return str(cand)
    return "organizer.db"


def get_areas_root_for_ingest(request: Request) -> Path:
    config = getattr(request.app.state, "config", None)
    if config and getattr(config, "areas_root_path", None):
        return Path(config.areas_root_path)
    return Path("areas")


def extract_preview_metadata(
    pdf_source: Union[str, Path, bytes],
    area_id: Optional[str] = None,
    house_id: Optional[str] = None,
    repo: Optional[Repository] = None,
    llm_client: Any = None,
    filename: Optional[str] = None,
) -> AIPreviewResponse:
    if isinstance(pdf_source, bytes):
        try:
            doc = fitz.open(stream=pdf_source, filetype="pdf")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid or corrupted PDF file: {e}")
    else:
        try:
            doc = fitz.open(str(pdf_source))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid or corrupted PDF file: {e}")

    try:
        page_count = len(doc)
        if page_count == 0:
            raise HTTPException(status_code=400, detail="PDF contains zero pages.")

        pages_text = []
        for p_idx in range(min(3, page_count)):
            pages_text.append(doc[p_idx].get_text() or "")
        full_text = "\n".join(pages_text).strip()
    finally:
        doc.close()

    # Unicode NFKC normalization and formatting cleanup
    full_text = unicodedata.normalize("NFKC", full_text)
    full_text = full_text.replace("\xad", "-").replace("\xa0", " ")

    # Digits normalization: Eastern Arabic-Indic numerals (٠-٩) to Latin digits (0-9)
    ar_to_en_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    text_normalized = full_text.translate(ar_to_en_digits)

    # Provide dual-orientation text so both standard logical and reversed visual-order Arabic match seamlessly
    reversed_lines = [line[::-1] for line in text_normalized.splitlines()]
    searchable_text = text_normalized + "\n" + "\n".join(reversed_lines)

    # 1. Date extraction
    suggested_date = None
    ar_months = {
        "يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4, "مايو": 5, "يونيو": 6,
        "يوليو": 7, "أغسطس": 8, "سبتمبر": 9, "أكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12
    }
    m_ar = re.search(
        r"\b(\d{1,2})\s+(يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+(\d{4})\b",
        searchable_text
    )
    if m_ar:
        d = int(m_ar.group(1))
        m = ar_months.get(m_ar.group(2), 1)
        y = int(m_ar.group(3))
        suggested_date = f"{y:04d}-{m:02d}-{d:02d}"

    if not suggested_date:
        m_iso = re.search(r"(?<!\d)(19\d{2}|20\d{2})[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12]\d|3[01])(?!\d)", text_normalized)
        if m_iso:
            y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
            if 1 <= m <= 12 and 1 <= d <= 31:
                suggested_date = f"{y:04d}-{m:02d}-{d:02d}"

    if not suggested_date:
        m_dmy = re.search(r"(?<!\d)(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|1[0-2])[-/.](19\d{2}|20\d{2})(?!\d)", text_normalized)
        if m_dmy:
            d, m, y = int(m_dmy.group(1)), int(m_dmy.group(2)), int(m_dmy.group(3))
            if 1 <= m <= 12 and 1 <= d <= 31:
                suggested_date = f"{y:04d}-{m:02d}-{d:02d}"

    if suggested_date:
        suggested_date = normalize_date(suggested_date)

    # 2. Category extraction (bilingual + normal/reversed Arabic)
    category_rules = [
        ("05-عقود", ["عقد", "دقع", "إيجار", "راجيإ", "اتفاقية", "تأجير", "شروط العقد", "contract", "contracts", "lease", "agreement", "طرف أول", "طرف ثاني"]),
        ("06-كهرباء وماء", ["كهرباء", "ءابرهك", "ماء", "فاتورة", "ةروطاف", "فواتير", "استهلاك", "هيئة الكهرباء", "ewa", "electricity", "water", "utility", "bill", "حساب كهرباء"]),
        ("03-أمر تخصيص", ["أمر تخصيص", "تخصيص مسكن", "تخصيص وحدة", "قرار تخصيص", "تسكين", "وزارة الإسكان", "allocation", "allotment", "amar takhsees"]),
        ("04-محضر تسليم مفتاح", ["تسليم مفتاح", "محضر تسليم", "استلام مفتاح", "تسليم المسكن", "مفاتيح", "key handover", "keys"]),
        ("07-استقطاع إيجار", ["استقطاع إيجار", "استقطاع شهري", "خصم إيجار", "استقطاع", "rent deduction", "salary deduction"]),
        ("08-وقف استقطاع بدل", ["وقف استقطاع", "بدل سكن", "وقف بدل", "stop allowance", "allowance"]),
        ("10-صيانة", ["صيانة", "ةنايص", "إصلاح", "ترميم", "عطل", "تسريب", "كهربائي", "سباكة", "maintenance", "repair"]),
        ("02-بيانات شخصية", ["بطاقة هوية", "جواز سفر", "جواز", "عقد زواج", "رخصة قيادة", "cpr", "passport", "id card", "personal details"]),
        ("01-بيانات أساسية", ["بيانات أساسية", "استمارة", "إقرار", "طلب سكن", "براءة ذمة", "تقرير حالة", "basic details", "application form"]),
        ("12-تعديلات", ["تعديل", "تعديلات", "إضافة غرفة", "كراج", "بناء ملحق", "توسعة", "modification", "modifications", "renovation"]),
        ("11-صور ومعاينات", ["معاينة", "تقرير معاينة", "صور", "كشف ميداني", "inspection", "pictures", "photos"]),
        ("09-إشعارات", ["إشعار", "إنذار", "تنبيه", "إخلاء", "warning", "notice", "eviction"]),
    ]

    lower_text = searchable_text.lower()
    best_category = None
    max_score = 0
    for cat, keywords in category_rules:
        score = sum(1 for kw in keywords if kw in lower_text)
        if score > max_score:
            max_score = score
            best_category = cat

    suggested_category = best_category if max_score > 0 else "13-رسائل متنوعة"

    # 3. Suggested title
    subject_match = re.search(r"(?:الموضوع|بشأن|subject)\s*[:/–—\-]\s*([^\n\r]+)", searchable_text, re.IGNORECASE)
    if subject_match:
        subj = subject_match.group(1).strip()
        if 3 <= len(subj) <= 80:
            suggested_title = subj
        else:
            suggested_title = None
    else:
        suggested_title = None

    if not suggested_title:
        category_titles = {
            "05-عقود": "عقد إيجار",
            "06-كهرباء وماء": "فاتورة كهرباء وماء",
            "03-أمر تخصيص": "أمر تخصيص مسكن",
            "04-محضر تسليم مفتاح": "محضر تسليم مفتاح",
            "07-استقطاع إيجار": "إشعار استقطاع إيجار",
            "08-وقف استقطاع بدل": "طلب وقف استقطاع بدل سكن",
            "10-صيانة": "طلب صيانة وإصلاح",
            "02-بيانات شخصية": "وثيقة بيانات شخصية",
            "01-بيانات أساسية": "استمارة بيانات أساسية",
            "12-تعديلات": "طلب تعديلات على المسكن",
            "11-صور ومعاينات": "تقرير معاينة وصور",
            "09-إشعارات": "إشعار رسمي",
            "13-رسائل متنوعة": "مستند رسمي",
        }
        suggested_title = category_titles.get(suggested_category, "مستند رسمي")
        if filename and Path(filename).stem and Path(filename).stem.lower() not in ("scan", "document", "upload", "test", "file"):
            suggested_title = f"{suggested_title} - {Path(filename).stem}"

    # 4. Tenant name suggestion
    clean_house = extract_house_id(house_id) if house_id else None
    suggested_tenant_name = None
    if repo and clean_house:
        try:
            tenants = repo.list_tenants_by_house(clean_house)
            for t in tenants:
                t_name = t.name.strip()
                if t_name and t_name in searchable_text:
                    suggested_tenant_name = t_name
                    break
        except Exception:
            pass

    if not suggested_tenant_name:
        tenant_match = re.search(
            r"(?:المستأجر|السيد|المواطن|الاسم|Tenant|Name)\s*[:/–—\-]\s*([^\n\r,–—\(\)]+)",
            searchable_text,
            re.IGNORECASE,
        )
        if tenant_match:
            raw_name = tenant_match.group(1).strip()
            for suffix in ["المحترم", "حفظه الله", "ورعاه", "وفقه الله"]:
                raw_name = raw_name.replace(suffix, "").strip()
            if 2 <= len(raw_name) <= 60:
                suggested_tenant_name = raw_name

    # 5. House number and Area
    suggested_house_id = clean_house
    if not suggested_house_id:
        house_match = re.search(r"(?:منزل|بيت|شقة|House|Villa|Unit)\s*(?:رقم|#)?\s*(\d+)", searchable_text, re.IGNORECASE)
        if house_match:
            suggested_house_id = house_match.group(1)

    suggested_area_id = area_id

    # 6. Optional LLM enhancement
    if llm_client is not None and hasattr(llm_client, "generate_content"):
        try:
            prompt = (
                "Analyze the following Arabic document text and provide suggestions in JSON format with fields: "
                "suggested_title, suggested_category, suggested_date, suggested_tenant_name, suggested_house_id.\n"
                f"Document text:\n{text_normalized[:1500]}"
            )
            res = llm_client.generate_content(contents=[prompt])
            if hasattr(res, "suggested_title") and res.suggested_title:
                suggested_title = res.suggested_title
            if hasattr(res, "suggested_category") and res.suggested_category:
                suggested_category = res.suggested_category
            if hasattr(res, "suggested_date") and res.suggested_date:
                suggested_date = res.suggested_date
            if hasattr(res, "suggested_tenant_name") and res.suggested_tenant_name:
                suggested_tenant_name = res.suggested_tenant_name
            if hasattr(res, "suggested_house_id") and res.suggested_house_id:
                suggested_house_id = res.suggested_house_id
        except Exception as e:
            pass

    return AIPreviewResponse(
        status="success",
        page_count=page_count,
        suggested_title=suggested_title,
        suggested_category=suggested_category,
        suggested_date=suggested_date,
        suggested_tenant_name=suggested_tenant_name,
        suggested_house_id=suggested_house_id,
        suggested_area_id=suggested_area_id,
    )


@router.post("/api/ingest/preview-ai", response_model=AIPreviewResponse)
async def preview_ai(
    request: Request,
    file: UploadFile = File(...),
    area_id: Optional[str] = Form(None),
    house_id: Optional[str] = Form(None),
):
    """Analyze single document text and return metadata predictions without committing to DB or vault."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files (.pdf) are supported."
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. File does not begin with %PDF header."
        )

    repo = get_db_repo(request)
    llm_client = getattr(request.app.state, "llm_client", None)

    return extract_preview_metadata(
        pdf_source=content,
        area_id=area_id,
        house_id=house_id,
        repo=repo,
        llm_client=llm_client,
        filename=file.filename,
    )


@router.post("/api/ingest", response_model=IngestResponse)
async def ingest_document(
    request: Request,
    file: UploadFile = File(...),
    mode: str = Form("manual"),
    area_id: str = Form(...),
    house_id: str = Form(...),
    tenant_id: Optional[int] = Form(None),
    tenant_name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    arabic_title: Optional[str] = Form(None),
    primary_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    dry_run: bool = Form(False),
):
    """Unified document ingestion endpoint supporting manual, assisted, and auto_split modes."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files (.pdf) are supported."
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. File does not begin with %PDF header."
        )

    valid_modes = {"manual", "assisted", "auto_split"}
    if mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{mode}'. Supported modes: {', '.join(sorted(valid_modes))}"
        )

    repo = get_db_repo(request)
    if not repo:
        db_path_candidate = get_db_path_for_ingest(request)
        if Path(db_path_candidate).exists():
            from src.db.connection import get_db_connection
            from src.db.schema import init_db
            conn = get_db_connection(db_path_candidate)
            init_db(conn)
            repo = Repository(conn)
            request.app.state.repo = repo
            request.app.state.db_path = db_path_candidate

    if not repo:
        raise HTTPException(status_code=503, detail="Database not connected.")

    db_path = get_db_path_for_ingest(request)
    areas_root = get_areas_root_for_ingest(request)
    clean_house_id = extract_house_id(house_id)

    # Ensure Area and House exist in DB
    if not repo.get_area(area_id):
        repo.add_area(area_id=area_id)
    if not repo.get_house(clean_house_id):
        repo.add_house(house_id=clean_house_id, area_id=area_id)
    if not repo.autocommit:
        repo.conn.commit()

    temp_dir = Path(tempfile.mkdtemp(prefix="api_ingest_"))
    original_name = Path(file.filename).name if file.filename else f"upload_{uuid.uuid4().hex[:8]}.pdf"
    temp_pdf_path = temp_dir / original_name

    try:
        temp_pdf_path.write_bytes(content)

        if mode == "auto_split":
            llm_client = getattr(request.app.state, "llm_client", None)
            try:
                result = ingest_pdf_to_house(
                    pdf_path=temp_pdf_path,
                    house_id=clean_house_id,
                    area_id=area_id,
                    db_path=Path(db_path),
                    areas_root=Path(areas_root),
                    llm_client=llm_client,
                    dry_run=dry_run,
                )
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Auto-split ingestion failed: {e}")

            clear_tree_cache()
            return IngestResponse(
                status="success",
                mode="auto_split",
                vault_ids=result.get("vault_ids", []),
                batch_id=result.get("batch_id"),
                page_count=result.get("pages_ingested", 0),
                documents_created=result.get("documents_created", 1),
                house_id=clean_house_id,
                area_id=area_id,
                message=f"Batch successfully auto-split into {result.get('documents_created', 1)} documents.",
            )

        if mode == "assisted":
            needs_preview = (
                not category or not category.strip()
                or not arabic_title or not arabic_title.strip()
                or not primary_date or not primary_date.strip()
                or (tenant_id is None and (not tenant_name or not tenant_name.strip()))
            )
            if needs_preview:
                preview = extract_preview_metadata(
                    pdf_source=temp_pdf_path,
                    area_id=area_id,
                    house_id=clean_house_id,
                    repo=repo,
                    llm_client=getattr(request.app.state, "llm_client", None),
                    filename=original_name,
                )
                if not category or not category.strip():
                    category = preview.suggested_category or "13-رسائل متنوعة"
                if not arabic_title or not arabic_title.strip():
                    arabic_title = preview.suggested_title or Path(original_name).stem
                if not primary_date or not primary_date.strip():
                    primary_date = preview.suggested_date
                if tenant_id is None and (not tenant_name or not tenant_name.strip()) and preview.suggested_tenant_name:
                    tenant_name = preview.suggested_tenant_name

        # Manual / assisted defaults
        if not category or not category.strip():
            category = "13-رسائل متنوعة"
        else:
            category = category.strip()

        if not arabic_title or not arabic_title.strip():
            arabic_title = Path(original_name).stem
        else:
            arabic_title = arabic_title.strip()

        primary_date = primary_date.strip() if (primary_date and primary_date.strip()) else None

        # Resolve tenant
        if tenant_name and tenant_name.strip() and tenant_id is None:
            existing_tenants = repo.list_tenants_by_house(clean_house_id)
            target_tenant = next((t for t in existing_tenants if t.name.strip().lower() == tenant_name.strip().lower()), None)
            if target_tenant:
                resolved_tenant_id = target_tenant.id
            else:
                new_t = repo.add_tenant(
                    house_id=clean_house_id,
                    name=tenant_name.strip(),
                    start_date=primary_date or date.today().isoformat(),
                    end_date=None,
                )
                if not repo.autocommit:
                    repo.conn.commit()
                resolved_tenant_id = new_t.id
        elif tenant_id is None and (not tenant_name or not tenant_name.strip()):
            active_t = repo.get_active_tenant(clean_house_id, target_date=primary_date)
            if active_t:
                resolved_tenant_id = active_t.id
            else:
                existing_tenants = repo.list_tenants_by_house(clean_house_id)
                if existing_tenants:
                    resolved_tenant_id = existing_tenants[0].id
                else:
                    def_t = repo.add_tenant(
                        house_id=clean_house_id,
                        name="Default Tenant",
                        start_date="1970-01-01",
                        end_date=None,
                    )
                    if not repo.autocommit:
                        repo.conn.commit()
                    resolved_tenant_id = def_t.id
        else:
            t = repo.get_tenant(tenant_id)
            if not t:
                raise HTTPException(status_code=400, detail=f"Tenant ID {tenant_id} does not exist.")
            if str(t.house_id) != str(clean_house_id):
                raise HTTPException(status_code=400, detail=f"Tenant {tenant_id} belongs to house '{t.house_id}', not '{clean_house_id}'.")
            resolved_tenant_id = tenant_id

        try:
            result = ingest_document_manual(
                pdf_path=temp_pdf_path,
                house_id=clean_house_id,
                area_id=area_id,
                tenant_id=resolved_tenant_id,
                category=category,
                arabic_title=arabic_title,
                primary_date=primary_date,
                db_path=db_path,
                areas_root=areas_root,
                notes=notes.strip() if notes else None,
                dry_run=dry_run,
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

        clear_tree_cache()
        v_id = result.get("vault_id")
        return IngestResponse(
            status="success",
            mode=mode,
            vault_id=v_id,
            vault_ids=[v_id] if v_id else None,
            batch_id=result.get("batch_id"),
            page_count=result.get("page_count", 0),
            documents_created=1,
            house_id=clean_house_id,
            area_id=area_id,
            message=f"Document successfully ingested {mode}ly into house {clean_house_id}.",
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


