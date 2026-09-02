"""Pydantic models for the API endpoints."""
from pydantic import BaseModel

class HouseResponse(BaseModel):
    id: str
    name: str

class VaultFileResponse(BaseModel):
    vault_id: str
    filename: str
    start_page: int
    end_page: int
    date: str
    tenant: str

class CategoryResponse(BaseModel):
    name: str
    document_count: int

class TimelineGroupResponse(BaseModel):
    vault_id: str
    primary_tenant: str
    dates: list[str]
    brief_arabic_title: str

class TreeItemResponse(BaseModel):
    id: str
    name: str
    type: str
    children: list["TreeItemResponse"] | None = None

class SearchResultResponse(BaseModel):
    id: str
    type: str # "house" or "tenant"
    title: str
    subtitle: str | None = None
    url: str # path to navigate to
