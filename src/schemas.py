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
    resident: str = Field(description="The resident name in Arabic, or 'NONE' for general house letters and Amar Takhsees")
    category: Category = Field(description="The document category from the 13 defined types")
    date: str = Field(description="The date of the document (Gregorian or Hijri) if visible, otherwise 'NONE'")

    @field_validator('resident', mode='before')
    @classmethod
    def normalize_resident(cls, v: str) -> str:
        """Strip whitespace and uppercase so ' none ' becomes 'NONE'."""
        if isinstance(v, str):
            return v.strip().upper()
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


class EntityResolutionMapping(BaseModel):
    """Schema for mapping raw extracted names to a Canonical Primary Tenant."""
    mapping: dict[str, str] = Field(description="Map of raw extracted name to canonical Arabic Primary Tenant Name")
