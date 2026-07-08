"""Router logic for assigning document groups to folders."""

import logging
from typing import Any
from pydantic import BaseModel, Field, field_validator, ValidationInfo, ValidationError
from src.core.schemas import DocumentGroup
from src.llm.llm import LLMFailureError
from src.processing.routing.config import CATEGORY_TO_FOLDERS, SINGLE_MATCH

logger = logging.getLogger(f"file_organizer.{__name__}")

consecutive_routing_failures = 0

class RoutingValidationError(Exception):
    """Exception raised when LLM fails to provide a valid folder after multiple attempts."""
    pass

class RoutingResponse(BaseModel):
    selected_folder: str = Field(description="The exact name of the selected folder from the allowed list")
    reason: str = Field(description="Explanation of why this folder was selected")

    @field_validator('selected_folder')
    @classmethod
    def validate_folder(cls, v: str, info: ValidationInfo) -> str:
        allowed = info.context.get('allowed_folders', []) if info.context else []
        if v not in allowed:
            raise ValueError(f"Selected folder '{v}' is not in the allowed list: {allowed}")
        return v

def route_document(group: DocumentGroup, llm_client: Any) -> tuple[str, bool]:
    """Route a document group to the appropriate folder.
    
    Args:
        group: The document group to route.
        llm_client: The LLM client to use for multi-match resolution.
        
    Returns:
        tuple[str, bool]: (folder_name, is_direct_routed)
    """
    category = group.category
    
    global consecutive_routing_failures
    if consecutive_routing_failures >= 5:
        logger.warning("Skipping LLM routing due to 5 consecutive failures.")
        return "13_others", False
        
    if category in SINGLE_MATCH:
        # Should have exactly one
        try:
            folder = CATEGORY_TO_FOLDERS[category][0]
            return folder, True
        except IndexError:
            logger.exception(f"IndexError: No folder mapping found for SINGLE_MATCH category '{category}'. Falling back.")
            return "Unassigned", False
        
    allowed_folders = CATEGORY_TO_FOLDERS.get(category, []).copy()
    if not allowed_folders:
        logger.warning(f"Category '{category}' has no mapping, falling back to 13_others")
        return "13_others", False
        
    if "13_others" not in allowed_folders:
        allowed_folders.append("13_others")
        
    # Multi-match routing via LLM
    from src.core.config import GEMINI_MODEL
    
    prompt_template = """You are an expert document routing assistant.
Your task is to assign a document to the most appropriate folder based on its summary, and explain why the document fits into the selected folder based on the summary.

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
    
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            # Pass validation_context for Pydantic enforcement
            result = llm_client.generate_content(
                contents=contents,
                response_schema=RoutingResponse,
                validation_context={'allowed_folders': allowed_folders}
            )
            
            if result is None:
                logger.warning(f"LLM routing returned None on attempt {attempt}.")
                continue
                
            selected = result.selected_folder
            reason = result.reason
            
            consecutive_routing_failures = 0
            logger.info(f"Routed category '{category}' to '{selected}'. Reason: {reason}")
            from src.logger import log_decision_trace
            log_decision_trace("routing", {"category": category, "selected": selected, "reason": reason})
            return selected, False
            
        except (ValidationError, ValueError) as e:
            # This is a schema/validation failure (e.g. folder not in allowed list)
            logger.warning(f"LLM routing validation failed on attempt {attempt}: {e}")
            
            if attempt < attempts:
                # Extract the rejected value from the error if possible for better feedback
                rejected_value = "unknown"
                if hasattr(e, 'errors'):
                    # Look for the value in the first error
                    err = e.errors()[0]
                    # Pydantic v2: the input is often in the 'input' field of the error
                    rejected_value = err.get('input', 'unknown')
                
                feedback = (
                    f"\n\nThis is a retry. Your previous response selected '{rejected_value}', "
                    f"which was rejected because it was not in the allowed list. "
                    f"Please choose strictly from:\n{formatted_prompt.split('Allowed Folders for this document type:')[1].split('Folder meanings:')[0].strip()}"
                )
                # Append feedback to the user prompt part of the contents
                contents[1] = contents[1] + feedback
            else:
                # 3rd attempt failed
                logger.error(f"LLM routing failed validation after {attempts} attempts for category {category}.")
                raise RoutingValidationError(f"Failed to route document to valid folder after {attempts} attempts. Last error: {e}")
                
        except LLMFailureError:
            # Infrastructure failure - re-raise to let the pipeline handle it (likely stop)
            raise
        except Exception as e:
            # Unexpected failure - treat as a retryable event unless it's the last attempt
            logger.warning(f"LLM routing unexpected failure on attempt {attempt}: {e}")
            if attempt == attempts:
                logger.error(f"LLM routing encountered an unexpected error on the final attempt for category {category}.")
                raise RoutingValidationError(f"Unexpected error during routing after {attempts} attempts: {e}")
            
    # This part is theoretically unreachable due to the raise in the loop
    return "13_others", False
