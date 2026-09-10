"""Domain models for the SQLite database layer."""

from datetime import date, datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class Area(BaseModel):
    """Area entity model."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: Optional[str] = None


class House(BaseModel):
    """House entity model."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    area_id: str


class Tenant(BaseModel):
    """Tenant entity model."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    house_id: str
    name: str
    start_date: Union[str, date]
    end_date: Optional[Union[str, date]] = None


class Batch(BaseModel):
    """Batch entity model for scanned document files."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    house_id: str
    filename: str
    file_path: str
    page_count: int
    status: str = "completed"
    created_at: Optional[Union[str, datetime]] = None


class Document(BaseModel):
    """Document entity model in the vault."""
    model_config = ConfigDict(from_attributes=True)

    vault_id: str
    house_id: str
    tenant_id: int
    batch_id: int
    primary_date: Optional[Union[str, date]] = None
    arabic_title: Optional[str] = None
    category: Optional[str] = None
    page_count: int = 1
    is_manual: int = 0
    notes: Optional[str] = None
    is_timeline_visible: int = 1
    created_at: Optional[Union[str, datetime]] = None


class Page(BaseModel):
    """Page entity model for individual scanned pages."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    batch_id: int
    page_number: int
    house_id: str
    category: Optional[str] = None
    content_explanation: Optional[str] = None
    expected_tenant_name: Optional[str] = None
    expected_house_number: Optional[str] = None
    raw_date: Optional[str] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    subject: Optional[str] = None
    is_continuation: bool = False
    tenant_id: Optional[int] = None
    resolved_date: Optional[Union[str, date]] = None
    fine_category: Optional[str] = None
    fine_category_reason: Optional[str] = None
    vault_id: Optional[str] = None
