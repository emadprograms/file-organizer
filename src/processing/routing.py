"""Routing logic for organizing document groups into destination folders."""

import logging
from typing import Any
from pydantic import BaseModel, Field
from src.core.schemas import DocumentGroup

log = logging.getLogger(__name__)

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
MULTI_MATCH = {cat for cat, folders in CATEGORY_TO_FOLDERS.items() if len(folders) > 1}

class RoutingResponse(BaseModel):
    selected_folder: str = Field(description="The exact name of the selected folder from the allowed list")

def route_document(group: DocumentGroup, llm_client: Any) -> tuple[str, bool]:
    """Route a document group to the appropriate folder.
    
    Args:
        group: The document group to route.
        llm_client: The LLM client to use for multi-match resolution.
        
    Returns:
        tuple[str, bool]: (folder_name, is_direct_routed)
    """
    category = group.category
    
    if category in SINGLE_MATCH:
        # Should have exactly one
        folder = CATEGORY_TO_FOLDERS[category][0]
        return folder, True
        
    allowed_folders = CATEGORY_TO_FOLDERS.get(category, []).copy()
    if not allowed_folders:
        log.warning(f"Category '{category}' has no mapping, falling back to 13_others")
        return "13_others", False
        
    if "13_others" not in allowed_folders:
        allowed_folders.append("13_others")
        
    # Multi-match routing via LLM
    from src.core.config import GEMINI_MODEL
    
    prompt_template = """You are an expert document routing assistant.
Your task is to assign a document to the most appropriate folder based on its summary.

Allowed Folders for this document type:
{allowed_folders}

Folder meanings:
- 1_requests_and_applications: Forms requesting something (e.g. housing application, loan request)
- 3_housing_committee_decisions: Letters detailing committee decisions
- 4_financial_details: Letters or forms about payments, loans, installments, financial statements
- 6_ewa_related_letters: Electricity and water authority correspondence
- 7_maintenance: Letters or forms regarding house repairs and maintenance
- 8_complaints_and_violations: Letters or forms about complaints, violations, warnings
- 9_legal_correspondence: Court orders, legal notices
- 10_ministry_internal_memos: Memos within the ministry
- 12_tenant_correspondence: General letters to/from the tenant
- 13_others: Anything that does not clearly fit into the specific folders above

Respond only with a valid JSON matching the requested schema. The selected_folder MUST be exactly one of the allowed folders.
"""
    
    formatted_prompt = prompt_template.format(allowed_folders="\n".join(f"- {f}" for f in allowed_folders))
    
    user_prompt = f"Document Category: {category}\nDocument Title/Summary: {group.brief_arabic_title or 'N/A'}\nReasoning for group: {group.reason or 'N/A'}"
    
    contents = [formatted_prompt, user_prompt]
    
    for attempt in range(2): # Try once, and retry once
        try:
            result = llm_client._route_llm_call(
                model=GEMINI_MODEL,
                contents=contents,
                response_schema=RoutingResponse,
                log_prefix=f"RoutingLLM-Attempt{attempt+1}"
            )
            selected = result.selected_folder
            if selected in allowed_folders:
                return selected, False
            else:
                log.warning(f"LLM selected invalid folder: {selected}. Expected one of {allowed_folders}")
        except Exception as e:
            log.warning(f"LLM routing failed on attempt {attempt+1}: {e}")
            
    # Fallback after two failures
    log.warning(f"LLM routing failed twice for category {category}. Falling back to 13_others.")
    return "13_others", False
