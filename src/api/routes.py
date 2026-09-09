import json
import base64
import re
import difflib
import time
import shutil
import uuid
from pathlib import Path
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
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
)
from src.db.repository import (
    Repository,
    get_or_create_numbered_folder,
    update_document,
    copy_document,
    reset_document_manual_lock,
)

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

def phonetic_normalize(text: str) -> str:
    text = text.lower()
    ar_to_en = {
        'ا': '', 'أ': '', 'إ': '', 'آ': '', 'ى': '',
        'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h', 'خ': 'kh',
        'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
        'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'dh', 'ع': '', 'غ': 'gh',
        'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
        'ه': 'h', 'ة': 'h', 'و': '', 'ي': '', 'ئ': '', 'ؤ': '', 'ء': ''
    }
    res = []
    for char in text:
        res.append(ar_to_en.get(char, char))
    text = "".join(res)
    text = re.sub(r'[aeiouyw]', '', text)
    text = text.replace('ph', 'f').replace('ck', 'k').replace('c', 'k')
    text = text.replace('th', 't').replace('dh', 'd').replace('kh', 'k').replace('gh', 'g').replace('sh', 's')
    text = re.sub(r'(.)\1+', r'\1', text)
    return text.strip()

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
            WHERE d.house_id = ? OR d.house_id = ?
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
            tenant_profiles.append(HouseTenantProfile(
                id=t.id,
                name=t.name,
                start_date=str(t.start_date),
                end_date=str(t.end_date) if t.end_date else None,
                is_active=is_active,
                duration_str_ar=dur_str,
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
    return [
        TenantItem(
            id=t.id,
            name=t.name,
            start_date=str(t.start_date),
            end_date=str(t.end_date) if t.end_date else None,
            house_id=t.house_id,
        )
        for t in tenants
    ]

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

        # 2. Tenants matching q (with phonetic and fuzzy matching)
        cursor = conn.execute("""
            SELECT t.id, t.name as tenant_name, t.start_date, t.end_date, t.house_id, h.area_id
            FROM tenants t
            JOIN houses h ON t.house_id = h.id
            ORDER BY t.start_date DESC
        """)
        q_phonetic = phonetic_normalize(q)
        for t in cursor.fetchall():
            t_name = t["tenant_name"]
            t_lower = t_name.lower()
            t_phonetic = phonetic_normalize(t_lower)
            is_match = False
            if q in t_lower:
                is_match = True
            elif q in str(t["house_id"]).lower():
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
                s_yr = t["start_date"][:4] if t["start_date"] else ""
                e_yr = "Present" if not t["end_date"] or str(t["end_date"]).lower() == "present" else str(t["end_date"])[:4]
                tenure_str = f"{s_yr} - {e_yr}" if s_yr else ""
                sub_label = f"House {t['house_id']} ({tenure_str}) • {t['area_id']}" if tenure_str else f"House {t['house_id']} • {t['area_id']}"
                results.append(SearchResultResponse(
                    id=f"{t['house_id']}_{t_name}",
                    type="tenant",
                    title=t_name,
                    subtitle=sub_label,
                    url=f"/#/area/{t['area_id']}/house/{t['house_id']}",
                    area_id=t["area_id"],
                    house_id=t["house_id"],
                    tenant_name=t_name,
                    extra_info=tenure_str
                ))

        # 3. Documents matching arabic_title or category or content_explanation in pages
        cursor = conn.execute("""
            SELECT DISTINCT d.vault_id, d.arabic_title, d.category, d.primary_date, d.is_manual, d.house_id, h.area_id, t.name as tenant_name
            FROM documents d
            JOIN houses h ON d.house_id = h.id
            LEFT JOIN tenants t ON d.tenant_id = t.id
            LEFT JOIN pages p ON (p.vault_id = d.vault_id OR (p.vault_id IS NULL AND p.batch_id = d.batch_id))
            WHERE LOWER(COALESCE(d.arabic_title, '')) LIKE ?
               OR LOWER(COALESCE(d.category, '')) LIKE ?
               OR LOWER(COALESCE(p.content_explanation, '')) LIKE ?
               OR LOWER(COALESCE(p.subject, '')) LIKE ?
            ORDER BY d.primary_date DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"))

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

