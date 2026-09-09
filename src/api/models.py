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
    brief_arabic_title: str | None = None

class CategoryResponse(BaseModel):
    tenant: str
    name: str
    document_count: int
    documents: list[VaultFileResponse] = []

class TimelineGroupResponse(BaseModel):
    vault_id: str
    primary_tenant: str
    dates: list[str]
    brief_arabic_title: str

class TreeItemResponse(BaseModel):
    id: str
    name: str
    type: str
    subtitle: str | None = None
    duration_category: str | None = None
    current_tenant: str | None = None
    total_documents: int | None = 0
    category_counts: dict[str, int] | None = None
    children: list["TreeItemResponse"] | None = None

class SearchResultResponse(BaseModel):
    id: str
    type: str # "house", "tenant", or "document"
    title: str
    subtitle: str | None = None
    url: str # path to navigate to

class TenantItem(BaseModel):
    id: int | None = None
    name: str
    start_date: str
    end_date: str | None = None
    house_id: str | None = None

class TenantBulkUpdateRequest(BaseModel):
    tenants: list[TenantItem]
    reallocate: bool = True

class TenantReallocationResponse(BaseModel):
    status: str
    reallocated_count: int
    total_documents: int
    tenants_count: int

class DocumentTenantUpdateRequest(BaseModel):
    tenant_id: int

