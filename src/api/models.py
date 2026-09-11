"""Pydantic models for the API endpoints."""
from typing import Optional
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
    tenant_id: int | None = None
    category: str | None = None
    brief_arabic_title: str | None = None
    is_manual: int = 0
    notes: str | None = None

class CategoryResponse(BaseModel):
    tenant: str
    name: str
    document_count: int
    documents: list[VaultFileResponse] = []

class TimelineGroupResponse(BaseModel):
    vault_id: str
    primary_tenant: str
    tenant_id: int | None = None
    dates: list[str]
    brief_arabic_title: str
    category: str | None = None
    is_manual: int = 0
    notes: str | None = None

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
    type: str  # "house", "tenant", or "document"
    title: str
    subtitle: str | None = None
    url: str  # path to navigate to
    area_id: str | None = None
    house_id: str | None = None
    tenant_name: str | None = None
    category: str | None = None
    date: str | None = None
    vault_id: str | None = None
    is_manual: int | None = 0
    extra_info: str | None = None

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

class DocumentNotesRequest(BaseModel):
    notes: str = ""

class DocumentNotesResponse(BaseModel):
    status: str
    vault_id: str
    notes: str | None = None

class DocumentUpdateRequest(BaseModel):
    arabic_title: str | None = None
    category: str | None = None
    tenant_id: int | None = None
    primary_date: str | None = None
    is_manual: int | None = 1
    notes: str | None = None

class DocumentCopyRequest(BaseModel):
    target_category: str | None = None
    target_tenant_id: int | None = None
    target_title: str | None = None

class DocumentActionResponse(BaseModel):
    status: str
    vault_id: str
    arabic_title: str | None = None
    category: str | None = None
    tenant_id: int | None = None
    tenant_name: str | None = None
    is_manual: int = 1

class HouseTenantProfile(BaseModel):
    id: int
    name: str
    start_date: str
    end_date: str | None = None
    is_active: bool = False
    duration_str_ar: str = ""
    duration_category: str | None = None
    document_count: int = 0
    category_count: int = 0

class CategoryBreakdownItem(BaseModel):
    category: str
    document_count: int

class HouseArchiveProfile(BaseModel):
    total_documents: int = 0
    total_pages: int = 0
    batch_count: int = 0
    oldest_date: str | None = None
    newest_date: str | None = None
    timespan_years: int = 0
    timespan_str_ar: str = ""
    categories: list[CategoryBreakdownItem] = []

class HouseProfileResponse(BaseModel):
    house_id: str
    area_id: str
    tenants: list[HouseTenantProfile] = []
    archive: HouseArchiveProfile


class IngestResponse(BaseModel):
    status: str
    mode: str
    vault_id: str | None = None
    vault_ids: list[str] | None = None
    batch_id: int | None = None
    page_count: int
    documents_created: int = 1
    house_id: str
    area_id: str
    message: str


class AIPreviewResponse(BaseModel):
    status: str
    page_count: int
    suggested_title: str | None = None
    suggested_category: str | None = None
    suggested_date: str | None = None
    suggested_tenant_name: str | None = None
    suggested_house_id: str | None = None
    suggested_area_id: str | None = None


class BatchDeleteRequest(BaseModel):
    vault_ids: list[str]


class BatchDeleteResponse(BaseModel):
    status: str = "success"
    deleted_count: int
    vault_ids: list[str]


class BatchMoveRequest(BaseModel):
    vault_ids: list[str]
    target_category: str
    target_tenant_id: Optional[int] = None


class BatchMoveResponse(BaseModel):
    status: str = "success"
    moved_count: int
    target_category: str
    vault_ids: list[str]


class BatchCopyRequest(BaseModel):
    vault_ids: list[str]
    target_category: str
    target_tenant_id: Optional[int] = None


class BatchCopyResponse(BaseModel):
    status: str = "success"
    copied_count: int
    target_category: str
    new_vault_ids: list[str]


class CreateHouseRequest(BaseModel):
    house_id: str
    area_id: Optional[str] = None
    initial_tenant_name: Optional[str] = None
    start_date: Optional[str] = None


class CreateHouseResponse(BaseModel):
    status: str = "success"
    area_id: str
    house_id: str
    tenant_id: Optional[int] = None
    message: str
