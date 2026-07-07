"""Data schemas and models used across the File Categorizer application.

These schemas leverage Pydantic for validation and structured data representation.
"""
from dataclasses import dataclass
from pydantic import BaseModel, Field

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
    start_page: int = Field(description="First page index of this document group (0-indexed)")
    end_page: int = Field(description="Last page index of this document group (0-indexed, inclusive)")
    reason: str = Field(description="Why these pages belong together — what subject/content connects them")
    brief_arabic_title: str = Field(description="Short Arabic title describing this document group")

class GroupingResponse(BaseModel):
    """The structured response from the LLM for a single boundary detection chunk."""
    groups: list[GroupEntry] = Field(description="Array of document groups found in this chunk")
