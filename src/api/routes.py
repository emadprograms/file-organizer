import json
import re
import difflib
import time
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import ValidationError

from src.api.models import HouseResponse, VaultFileResponse, CategoryResponse, TimelineGroupResponse, TreeItemResponse, SearchResultResponse

router = APIRouter()

NOT_FOUND_DETAIL = "{\"error\": \"Resource not found.\", \"solution\": \"Verify the endpoint URL and the resource ID.\"}"

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
    if isinstance(routed, list) and routed:
        return routed
    if isinstance(grouped, list) and grouped:
        return grouped
    return []


@router.get("/api/houses", response_model=list[HouseResponse])
async def list_houses(request: Request):
    config = request.app.state.config
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
    config = request.app.state.config
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
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    state_path = areas_root / area_id / house_id / ".source_files" / f"{house_num}_state.json"

    if not state_path.exists():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state_data = json.load(f)
    except Exception:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    responses = []
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

    def get_sort_date(r: TimelineGroupResponse) -> str:
        if r.dates and r.dates[0] and r.dates[0] != "NONE":
            return r.dates[0]
        return "0000-00-00"
        
    responses.sort(key=get_sort_date, reverse=True)
    return responses

@router.get("/api/areas/{area_id}/houses/{house_id}/categories", response_model=list[CategoryResponse])
async def list_categories(request: Request, area_id: str, house_id: str):
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    state_path = areas_root / area_id / house_id / ".source_files" / f"{house_num}_state.json"

    if not state_path.exists():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state_data = json.load(f)
    except Exception:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    from src.routing.config import FOLDER_PREFIXES
    from src.api.models import VaultFileResponse

    categories: dict[tuple[str, str], list[VaultFileResponse]] = {}
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
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    pdf_path = areas_root / area_id / house_id / ".source_files" / "vault" / f"doc_{vault_id}.pdf"

    if not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return FileResponse(pdf_path, media_type="application/pdf")

def _house_sort_key(entry: Path) -> tuple[int, str]:
    match = re.search(r'(\d+)', entry.name)
    num = int(match.group(1)) if match else 999999999
    return (num, entry.name)

@router.get("/api/tree", response_model=list[TreeItemResponse])
async def get_tree(request: Request):
    """
    Walk the real 3-level disk structure:
        areas_root/
            <Area folder>/     <- child of areas_root; name matches area_mappings key
                <House folder>/ <- child of Area; e.g. "1245 - Ali"
                    .source_files/
                        <id>_state.json
    """
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    if not areas_root.exists():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    area_mappings = config.area_mappings or {}

    areas: dict[str, TreeItemResponse] = {}

    for area_entry in sorted(areas_root.iterdir()):
        if not area_entry.is_dir():
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
            if not house_entry.is_dir():
                continue

            house_dir_name = house_entry.name   # e.g. "1245 - Ali"
            house_id = house_dir_name.split(" - ")[0] if " - " in house_dir_name else house_dir_name

            house_node = TreeItemResponse(
                id=house_dir_name,
                name=house_dir_name,
                type="house",
                children=[]
            )

            state_path = house_entry / ".source_files" / f"{house_id}_state.json"
            tenants_with_dates: dict[str, set[int]] = {}
            tenant_is_present: dict[str, bool] = {}
            if state_path.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                    
                    per_page = state_data.get("manifest", {}).get("per_page", [])
                    for doc in per_page:
                        tenant = doc.get("tenant")
                        if tenant:
                            tf = doc.get("target_folder", "")
                            if "الآن" in tf or "present" in tf.lower():
                                tenant_is_present[tenant] = True
                    
                    for group in _get_document_groups(state_data):
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

            current_year = datetime.now().year
            for t, years in sorted(tenants_with_dates.items()):
                subtitle = None
                is_long_term = False
                if years:
                    min_val = min(years)
                    max_val = max(years)
                    
                    actual_max = current_year if tenant_is_present.get(t) else max_val
                    if actual_max - min_val > 5:
                        is_long_term = True

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
                    is_long_term=is_long_term,
                    type="tenant"
                ))

            areas[area_name].children.append(house_node)

    return list(areas.values())

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
            if state_path.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state_data = json.load(f)

                    house_tenants: set[str] = set()
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

    config = request.app.state.config
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
                url=f"/#/area/{h['area_name']}/house/{h['house_dir_name']}"
            ))
            
    for t in index["tenants"]:
        t_name = t["tenant_name"]
        t_lower = t_name.lower()
        is_match = False
        if q in t_lower:
            is_match = True
        else:
            if len(q.split()) == 1:
                if difflib.get_close_matches(q, t_lower.split(), n=1, cutoff=0.7):
                    is_match = True
            else:
                if difflib.SequenceMatcher(None, q, t_lower).ratio() >= 0.7:
                    is_match = True
        if is_match:
            results.append(SearchResultResponse(
                id=f"{t['house_dir_name']}_{t_name}",
                type="tenant",
                title=t_name,
                subtitle=f"Tenant in {t['house_dir_name']}",
                url=f"/#/area/{t['area_name']}/house/{t['house_dir_name']}/tenant/{t['house_dir_name']}_{t_name}"
            ))

    for d in index["documents"]:
        if q in d["content"] or q in d["title_field"]:
            results.append(SearchResultResponse(
                id=f"{d['house_dir_name']}_doc_{d['vault_id']}",
                type="document",
                title=d["doc_title"],
                subtitle=f"Document in {d['house_dir_name']}",
                url=f"/#/area/{d['area_name']}/house/{d['house_dir_name']}"
            ))

    seen: set[str] = set()
    unique_results = []
    for r in results:
        if r.id not in seen:
            seen.add(r.id)
            unique_results.append(r)

    return unique_results[:50]
