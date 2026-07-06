"""Data schemas and models used across the File Categorizer application.

These schemas leverage Pydantic for validation and structured data representation.
"""
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator




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


class NameMapping(BaseModel):
    """Mapping between a raw extracted name and its canonical representation."""
    raw_name: str = Field(description="The raw name as it appears in the log")
    canonical_name: str = Field(description="The canonical Arabic Primary Tenant name it resolves to")

class EntityResolutionMapping(BaseModel):
    """Schema for mapping raw extracted names to a Canonical Primary Tenant."""
    mapping_list: list[NameMapping] = Field(description="List of raw extracted name to canonical name mappings")

class NameMatchResult(BaseModel):
    """Structured output for semantic name matching."""
    is_match: bool = Field(description="True if the names semantically refer to the same person, False otherwise")
    reason: str = Field(description="The reasoning for the decision")

class DateOutlierDetectionResult(BaseModel):
    """Schema for LLM-based date outlier detection."""
    outlier_page_indices: list[int] = Field(description="List of page indices that contain dates which are clearly outliers in the document's chronological sequence.")

class BulkSemanticMatchResult(BaseModel):
    """Schema for bulk semantic grouping."""
    groups: list[list[int]] = Field(description="List of groups, where each group is a list of page numbers that belong together.")
