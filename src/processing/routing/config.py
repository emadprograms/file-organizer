"""Configuration for routing logic."""
import logging

logger = logging.getLogger(f"file_organizer.{__name__}")

FOLDER_ROUTING: dict[str, list[str]] = {
    "1_requests_and_applications": ["forms"],
    "2_personal_details": ["id_cards"],
    "3_housing_committee_decisions": ["letters"],
    "4_financial_details": ["forms", "letters"],
    "5_contract": ["contract"],
    "6_ewa_related_letters": ["utility_bills"],
    "7_maintenance": ["forms", "letters"],
    "8_complaints_and_violations": ["letters", "forms"],
    "9_legal_correspondence": ["letters"],
    "10_ministry_internal_memos": ["letters"],
    "11_inspection_and_pictures": ["pictures"],
    "12_tenant_correspondence": ["letters"],
    "13_others": ["others", "forms", "letters"],  # catch-all
}

CATEGORY_TO_FOLDERS: dict[str, list[str]] = {}
for folder, cats in FOLDER_ROUTING.items():
    for cat in cats:
        CATEGORY_TO_FOLDERS.setdefault(cat, []).append(folder)

SINGLE_MATCH = {cat for cat, folders in CATEGORY_TO_FOLDERS.items() if len(folders) == 1}
