"""Data schemas and models used across the File Categorizer application.

These schemas leverage Pydantic for validation and structured data representation.
"""
import logging
from pydantic import BaseModel, Field, AliasChoices

logger = logging.getLogger(f"file_organizer.{__name__}")

class DocumentGroup(BaseModel):
    """A group of consecutive pages belonging to the same document segment."""
    start_page: int
    end_page: int
    primary_tenant: str
    category: str
    dates: list[str]
    reason: str | None = None
    brief_arabic_title: str | None = None
    folder_path: str | None = None
    is_direct_routed: bool = False

class GroupEntry(BaseModel):
    """A document group defined by the LLM during the boundary detection phase."""
    reason: str = Field(description="Why these pages belong together — what subject/content connects them")
    brief_arabic_title: str = Field(
        description="Short Arabic title describing this document group",
        validation_alias=AliasChoices('brief_arabic_title', 'title', 'arabic_title', 'title_ar')
    )
    start_page: int = Field(description="First page index of this document group (0-indexed)")
    end_page: int = Field(description="Last page index of this document group (0-indexed, inclusive)")

class GroupingResponse(BaseModel):
    """The structured response from the LLM for a single boundary detection chunk."""
    groups: list[GroupEntry] = Field(
        description="Array of document groups found in this chunk",
        validation_alias=AliasChoices('groups', 'document_groups')
    )

class CategorizationResult(BaseModel):
    """The structured extraction result from the file categorization pass."""
    category: str = Field(description="The determined document category")
    content_explanation: str = Field(description="Detailed explanation of the document contents")
    expected_tenant_name: str | None = Field(None, description="The person living in or responsible for the house")
    expected_house_number: str | None = Field(None, description="The house number associated with the tenant")
    
    # Conditional fields based on category
    image_contents: str | None = Field(None, description="Core subject matter (for pictures)")
    sender: str | None = Field(None, description="Sender information (for letters)")
    receiver: str | None = Field(None, description="Recipient information (for letters)")
    subject: str | None = Field(None, description="Subject line (for letters)")
    date: str | None = Field(None, description="Date issued (for letters)")
    brief_summary: str | None = Field(None, description="Brief summary (for others)")
