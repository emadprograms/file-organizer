from typing import Optional
from pydantic import BaseModel

class PageData(BaseModel):
    category: str
    content_explanation: str
    expected_tenant_name: Optional[str] = None
    expected_house_number: Optional[str] = None
    date: Optional[str] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    subject: Optional[str] = None

    canonical_tenant: Optional[str] = None
    resolved_date: Optional[str] = None
    original_index: int

class TenantTimeline(BaseModel):
    canonical_name: str
    min_date: str
    max_date: str
