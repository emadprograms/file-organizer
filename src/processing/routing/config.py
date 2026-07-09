"""Configuration for routing logic."""
import logging
from typing import Any

logger = logging.getLogger(f"file_organizer.{__name__}")

FOLDER_ROUTING: dict[str, dict[str, Any]] = {
    "بيانات أساسية": {"cats": ["BASIC_DETAILS"], "desc": "Forms requesting basic details or personal info"},
    "بيانات شخصية": {"cats": ["PERSONAL_DETAILS"], "desc": "Personal details documents"},
    "أمر تخصيص": {"cats": ["AMAR_TAKHSEES"], "desc": "Letters detailing housing allocation decisions"},
    "محضر تسليم مفتاح": {"cats": ["KEY_HANDOVER"], "desc": "Forms for key handover"},
    "عقود": {"cats": ["CONTRACT"], "desc": "Contracts and agreements"},
    "كهرباء وماء": {"cats": ["EWA_LETTERS"], "desc": "Electricity and water authority correspondence"},
    "استقطاع إيجار": {"cats": ["RENT_DEDUCTION"], "desc": "Letters or forms about rent deductions"},
    "وقف استقطاع بدل": {"cats": ["ALLOWANCE_DEDUCTION"], "desc": "Letters or forms about stopping allowance deductions"},
    "إشعارات": {"cats": ["NOTIFICATIONS"], "desc": "Notifications and warnings"},
    "صيانة": {"cats": ["MAINTENANCE"], "desc": "Letters or forms regarding house repairs and maintenance"},
    "صور ومعاينات": {"cats": ["INSPECTION_PICTURES"], "desc": "Inspection pictures and reports"},
    "تعديلات": {"cats": ["MODIFICATIONS"], "desc": "Modification requests or approvals"},
    "رسائل متنوعة": {"cats": ["OTHER_LETTERS"], "desc": "Anything that does not clearly fit into the specific folders above"},
}

CATEGORY_TO_FOLDERS: dict[str, list[str]] = {}
for folder, data in FOLDER_ROUTING.items():
    for cat in data["cats"]:
        CATEGORY_TO_FOLDERS.setdefault(cat, []).append(folder)

FOLDER_PREFIXES: dict[str, str] = {
    "بيانات أساسية": "1",
    "بيانات شخصية": "2",
    "أمر تخصيص": "3",
    "محضر تسليم مفتاح": "4",
    "عقود": "5",
    "كهرباء وماء": "6",
    "استقطاع إيجار": "7",
    "وقف استقطاع بدل": "8",
    "إشعارات": "9",
    "صيانة": "10",
    "صور ومعاينات": "11",
    "تعديلات": "12",
    "رسائل متنوعة": "13",
}

# Groupings for constrained routing
FORM_CATEGORIES = {"BASIC_DETAILS", "KEY_HANDOVER", "MAINTENANCE", "MODIFICATIONS"}
FORM_FOLDERS = {"بيانات أساسية", "محضر تسليم مفتاح", "صيانة", "تعديلات", "رسائل متنوعة"}

LETTER_CATEGORIES = {"AMAR_TAKHSEES", "RENT_DEDUCTION", "ALLOWANCE_DEDUCTION", "NOTIFICATIONS"}
LETTER_FOLDERS = {"أمر تخصيص", "استقطاع إيجار", "وقف استقطاع بدل", "إشعارات", "كهرباء وماء", "رسائل متنوعة"}

SINGLE_MATCH = {cat for cat, folders in CATEGORY_TO_FOLDERS.items() if len(folders) == 1}

DIRECT_ROUTED_CATEGORIES = {
    "PERSONAL_DETAILS",
    "CONTRACT",
    "EWA_LETTERS",
    "INSPECTION_PICTURES",
}
