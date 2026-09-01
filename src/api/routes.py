import json
import re
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import ValidationError

from src.api.models import HouseResponse, VaultFileResponse, CategoryResponse, TimelineGroupResponse

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

@router.get("/api/houses/{house_id}/timeline", response_model=list[TimelineGroupResponse])
async def list_timeline(request: Request, house_id: str):
    validate_id(house_id, r"^[a-zA-Z0-9_\-\s]+$")
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    state_path = areas_root / house_id / ".source_files" / f"{house_id}_state.json"
    
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

@router.get("/api/houses/{house_id}/categories", response_model=list[CategoryResponse])
async def list_categories(request: Request, house_id: str):
    validate_id(house_id, r"^[a-zA-Z0-9_\-\s]+$")
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    state_path = areas_root / house_id / ".source_files" / f"{house_id}_state.json"
    tenants_path = areas_root / house_id / "tenants.yaml"
    
    if not state_path.exists():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
        
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state_data = json.load(f)
    except Exception:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
        
    counts = {}
    for group in state_data.get("grouped_documents", []):
        tenant = group.get("primary_tenant")
        cat = group.get("category")
        if tenant and cat:
            key = f"{tenant}/{cat}"
            counts[key] = counts.get(key, 0) + 1
            
    responses = [CategoryResponse(name=k, document_count=v) for k, v in counts.items()]
    return responses

@router.get("/api/houses/{house_id}/pdf/{vault_id}")
async def get_pdf(request: Request, house_id: str, vault_id: str):
    validate_id(house_id, r"^[a-zA-Z0-9_\-\s]+$")
    validate_id(vault_id, r"^[a-zA-Z0-9_-]+$")
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    
    pdf_path = areas_root / house_id / ".source_files" / "vault" / f"doc_{vault_id}.pdf"
    
    if not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
        
    return FileResponse(pdf_path, media_type="application/pdf")
