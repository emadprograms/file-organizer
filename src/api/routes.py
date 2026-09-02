import json
import base64
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

@router.get("/api/areas/{area_id}/houses/{house_id}/categories", response_model=list[CategoryResponse])
async def list_categories(request: Request, area_id: str, house_id: str):
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    house_num = house_id.split(" - ")[0] if " - " in house_id else house_id
    state_path = areas_root / area_id / house_id / ".source_files" / f"{house_num}_state.json"

    from src.routing.config import FOLDER_PREFIXES
    from src.api.models import VaultFileResponse
    
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
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    house_dir = areas_root / area_id / house_id
    if vault_id.startswith("fs_"):
        try:
            b64_str = vault_id[3:]
            b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
            rel_path = base64.urlsafe_b64decode(b64_str).decode('utf-8')
            pdf_path = house_dir / rel_path
        except Exception:
            raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    else:
        pdf_path = house_dir / ".source_files" / "vault" / f"doc_{vault_id}.pdf"

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
                duration_category = None
                if years:
                    min_val = min(years)
                    max_val = max(years)
                    
                    actual_max = current_year if tenant_is_present.get(t) else max_val
                    duration = actual_max - min_val
                    if duration < 5:
                        duration_category = "short"
                    elif duration < 10:
                        duration_category = "medium"
                    else:
                        duration_category = "long"

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
