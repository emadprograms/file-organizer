import json
import re
import difflib
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import ValidationError

from src.api.models import HouseResponse, VaultFileResponse, CategoryResponse, TimelineGroupResponse, TreeItemResponse, SearchResultResponse

router = APIRouter()

NOT_FOUND_DETAIL = "{\"error\": \"Resource not found.\", \"solution\": \"Verify the endpoint URL and the resource ID.\"}"

def validate_id(id_str: str, pattern: str) -> None:
    if not re.match(pattern, id_str):
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

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
    for group in state_data.get("grouped_documents", []):
        try:
            responses.append(TimelineGroupResponse(
                vault_id=group.get("vault_id", ""),
                primary_tenant=group.get("primary_tenant", "") or "",
                dates=group.get("dates", []),
                brief_arabic_title=group.get("brief_arabic_title", "")
            ))
        except ValidationError:
            pass
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

    counts: dict[str, int] = {}
    for group in state_data.get("grouped_documents", []):
        tenant = group.get("primary_tenant")
        cat = group.get("fine_category") or group.get("category")
        if tenant and cat:
            key = f"{tenant}/{cat}"
            counts[key] = counts.get(key, 0) + 1

    return [CategoryResponse(name=k, document_count=v) for k, v in counts.items()]

@router.get("/api/areas/{area_id}/houses/{house_id}/pdf/{vault_id}")
async def get_pdf(request: Request, area_id: str, house_id: str, vault_id: str):
    validate_id(vault_id, r"^[a-zA-Z0-9_-]+$")
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    pdf_path = areas_root / area_id / house_id / ".source_files" / "vault" / f"doc_{vault_id}.pdf"

    if not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    return FileResponse(pdf_path, media_type="application/pdf")


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
        for house_entry in sorted(area_entry.iterdir()):
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
            tenants: set[str] = set()
            if state_path.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                    for group in state_data.get("grouped_documents", []):
                        tenant = group.get("primary_tenant")
                        if tenant:
                            tenants.add(tenant)
                except Exception:
                    pass

            for t in sorted(tenants):
                house_node.children.append(TreeItemResponse(
                    id=f"{house_dir_name}_{t}",
                    name=t,
                    type="tenant"
                ))

            areas[area_name].children.append(house_node)

    return list(areas.values())

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

    # Walk: areas_root → Area folder → House folder
    for area_entry in sorted(areas_root.iterdir()):
        if not area_entry.is_dir():
            continue

        area_name = area_entry.name  # e.g. "Safra C"

        for house_entry in sorted(area_entry.iterdir()):
            if not house_entry.is_dir():
                continue

            house_dir_name = house_entry.name
            house_id = house_dir_name.split(" - ")[0] if " - " in house_dir_name else house_dir_name

            # Match house by name
            if q in house_dir_name.lower():
                results.append(SearchResultResponse(
                    id=house_dir_name,
                    type="house",
                    title=house_dir_name,
                    subtitle=f"House in {area_name}",
                    url=f"/#/area/{area_name}/house/{house_dir_name}"
                ))

            state_path = house_entry / ".source_files" / f"{house_id}_state.json"
            if state_path.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state_data = json.load(f)

                    tenants: set[str] = set()
                    for group in state_data.get("grouped_documents", []):
                        tenant = group.get("primary_tenant")
                        if tenant:
                            tenants.add(tenant)

                    for t in tenants:
                        t_lower = t.lower()
                        is_match = False
                        if q in t_lower:
                            is_match = True
                        else:
                            # Fuzzy match for typo tolerance
                            if len(q.split()) == 1:
                                if difflib.get_close_matches(q, t_lower.split(), n=1, cutoff=0.7):
                                    is_match = True
                            else:
                                if difflib.SequenceMatcher(None, q, t_lower).ratio() >= 0.7:
                                    is_match = True

                        if is_match:
                            results.append(SearchResultResponse(
                                id=f"{house_dir_name}_{t}",
                                type="tenant",
                                title=t,
                                subtitle=f"Tenant in {house_dir_name}",
                                url=f"/#/area/{area_name}/house/{house_dir_name}/tenant/{house_dir_name}_{t}"
                            ))
                except Exception:
                    pass

            report_path = house_entry / ".source_files" / f"{house_id}_report.json"
            if report_path.exists():
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_data = json.load(f)

                    for doc in report_data.get("documents", []):
                        content = doc.get("content", "").lower()
                        title_field = doc.get("brief_arabic_title", "").lower()
                        if q in content or q in title_field:
                            vault_id = doc.get("vault_id", "")
                            doc_title = doc.get("brief_arabic_title", "Document")
                            results.append(SearchResultResponse(
                                id=f"{house_dir_name}_doc_{vault_id}",
                                type="document",
                                title=doc_title,
                                subtitle=f"Document in {house_dir_name}",
                                url=f"/#/area/{area_name}/house/{house_dir_name}"
                            ))
                except Exception:
                    pass

    # Deduplicate by id, preserve order
    seen: set[str] = set()
    unique_results = []
    for r in results:
        if r.id not in seen:
            seen.add(r.id)
            unique_results.append(r)

    return unique_results[:50]
