from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    """13-category classification for Bahrain housing documents."""
    BASIC_DETAILS = "basic_details"
    PERSONAL_DETAILS = "personal_details"
    AMAR_TAKHSEES = "amar_takhsees"
    KEY_HANDOVER = "key_handover_form"
    CONTRACT = "contract"
    EWA_LETTERS = "ewa_related_letters"
    RENT_DEDUCTION = "rent_deduction"
    ALLOWANCE_DEDUCTION = "allowance_deduction"
    NOTIFICATIONS = "notifications"
    MAINTENANCE = "maintenance"
    PICTURES = "pictures"
    MODIFICATIONS = "modifications"
    OTHER_LETTERS = "other_letters"


class PageClassification(BaseModel):
    """Structured output schema for per-page document classification."""
    house_number: str = Field(description="The house number mentioned in the document")
    residents: list[str] = Field(description="List of resident names in Arabic, with relationship in parentheses if known (e.g. 'Name (Wife)'). Return ['NONE'] if no names.")
    category: Category = Field(description="The document category from the 13 defined types")
    date: str = Field(description="The date of the document (Gregorian or Hijri) if visible, otherwise 'NONE'")
    is_continuation: bool = Field(default=False, description="True if this page is a continuation of the previous page, False otherwise")

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
    house_number: str
    primary_tenant: str
    category: Category
    dates: list[str]


class NameMapping(BaseModel):
    raw_name: str = Field(description="The raw name as it appears in the log")
    canonical_name: str = Field(description="The canonical Arabic Primary Tenant name it resolves to")

class EntityResolutionMapping(BaseModel):
    """Schema for mapping raw extracted names to a Canonical Primary Tenant."""
    mapping_list: list[NameMapping] = Field(description="List of raw extracted name to canonical name mappings")
