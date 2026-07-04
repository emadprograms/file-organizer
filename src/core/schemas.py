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

class ConfigGrouping(BaseModel):
    strategy: str = Field(default="declarative", description="Grouping strategy to use ('declarative' or 'python')")
    group_by: list[str] | None = Field(default=None, description="Fields to group by if strategy is 'declarative'")
    script_path: str | None = Field(default=None, description="Path to python script if strategy is 'python'")

class ConfigRouting(BaseModel):
    strategy: str = Field(default="declarative", description="Routing strategy to use ('declarative' or 'python')")
    fallback_folder: str = Field(default="UNKNOWN", description="Fallback folder if resident is NONE")
    script_path: str | None = Field(default=None, description="Path to python script if strategy is 'python'")
    rules: dict[str, str] = Field(description="Mapping of category to destination folder")

class ConfigCleaning(BaseModel):
    strategy: str = Field(description="Cleaning strategy to use ('llm', 'python', or 'hybrid')")
    prompt_template: str | None = Field(default=None, description="Prompt template if strategy is 'llm'")
    script_path: str | None = Field(default=None, description="Path to python script if strategy is 'python'")
    prompts: dict[str, str] | None = Field(default=None, description="Dictionary of specific LLM prompts for cleaning steps")

class UserConfig(BaseModel):
    categories: list[ConfigCategory] = Field(description="List of document categories")
    extraction: ConfigExtraction = Field(description="Extraction instructions")
    cleaning: ConfigCleaning = Field(description="Cleaning strategy and rules")
    grouping: ConfigGrouping = Field(description="Grouping constraints and strategies")
    routing: ConfigRouting = Field(description="Routing and organization rules")
