"""Data schemas and models used across the File Categorizer application.

These schemas leverage Pydantic for validation and structured data representation.
"""
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    """13-category classification for Bahrain housing documents."""
    BASIC_DETAILS = "Basic Details Form"
    PERSONAL_DETAILS = "Personal Identification"
    AMAR_TAKHSEES = "Allocation Order"
    KEY_HANDOVER = "Key Handover Certificate"
    CONTRACT = "Housing Contract"
    EWA_LETTERS = "Electricity and Water"
    RENT_DEDUCTION = "Rent Deduction Notice"
    ALLOWANCE_DEDUCTION = "Allowance Deduction Notice"
    NOTIFICATIONS = "General Notifications"
    MAINTENANCE = "Maintenance Records"
    INSPECTION_PICTURES = "Inspection and Pictures"
    MODIFICATIONS = "Property Modifications"
    OTHER_LETTERS = "Miscellaneous Letters"


class PageClassification(BaseModel):
    """Structured output schema for per-page document classification."""
    residents: list[str] = Field(description="List of resident names in Arabic, with relationship in parentheses if known (e.g. 'Name (Wife)'). Return ['NONE'] if no names.")
    category: Category = Field(description="The document category from the 13 defined types")
    date: str = Field(description="The date of the document (Gregorian or Hijri) if visible, otherwise 'NONE'")
    summary: str = Field(description="A verbose, one-line 'full story' of the page content, e.g., 'This letter from Ministry of Housing is for Mohamed Ali regarding a request to build an additional room.' Do not be lazy; extract all key context.")

    @field_validator('category', mode='before')
    @classmethod
    def normalize_category(cls, v):
        """Normalize category string to enum values."""
        if isinstance(v, str):
            v_lower = v.lower().strip()
            for category in Category:
                if v_lower == category.value.lower() or v_lower == category.name.lower() or v_lower.replace('_', ' ') == category.value.lower():
                    return category.value
        return v

    @field_validator('residents', mode='before')
    @classmethod
    def normalize_resident(cls, v):
        """Strip whitespace and uppercase so ' none ' becomes 'NONE'."""
        if isinstance(v, str):
            v = [v]
        if isinstance(v, list):
            return [name.strip().upper() for name in v if isinstance(name, str)]
        return v


@dataclass
class DocumentGroup:
    """A group of consecutive pages belonging to the same document segment."""
    start_page: int
    end_page: int
    primary_tenant: str
    category: Category
    dates: list[str]


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

class ConfigCategory(BaseModel):
    id: str = Field(description="Category identifier mapping to Category enum")
    name: str = Field(description="Display name or destination folder name")

class ConfigField(BaseModel):
    name: str = Field(description="Name of the field to extract")
    type: str = Field(description="Type of the field (e.g., str, list[str])")
    description: str = Field(description="Description of the field for the LLM")

class ConfigExtraction(BaseModel):
    prompt_template: str = Field(description="Specific instructions for extracting data from documents")
    fields: list[ConfigField] = Field(description="Fields to extract")

class ConfigRouting(BaseModel):
    destination_format: str = Field(description="Format string for destination folders")

class UserConfig(BaseModel):
    categories: list[ConfigCategory] = Field(description="List of document categories")
    extraction: ConfigExtraction = Field(description="Extraction instructions")
    routing: ConfigRouting = Field(description="Routing and organization rules")
