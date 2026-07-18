from typing import Optional, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(f"file_organizer.{__name__}")

class PageData(BaseModel):
    """Data model representing a single parsed page from a document.
    
    Attributes:
        category (str): The document category.
        content_explanation (str): Explanation of the content.
        expected_tenant_name (Optional[str]): The extracted tenant name, if any.
        expected_house_number (Optional[str]): The extracted house number, if any.
        date (Optional[str]): The raw extracted date, if any.
        sender (Optional[str]): Sender of the document, if any.
        receiver (Optional[str]): Receiver of the document, if any.
        subject (Optional[str]): Subject of the document, if any.
        canonical_tenant (Optional[str]): The matched canonical tenant name.
        resolved_date (Optional[str]): The normalized YYYY-MM-DD date.
        original_index (int): The 0-based original index of the page in the document.
    """
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
    """Data model representing the active timeline for a canonical tenant.
    
    Attributes:
        canonical_name (str): The canonical name of the tenant.
        min_date (str): The earliest date associated with the tenant.
        max_date (str): The latest date associated with the tenant.
    """
    canonical_name: str
    min_date: str
    max_date: str
