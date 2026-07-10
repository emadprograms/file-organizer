"""Router logic for assigning document groups to folders."""

import logging
from typing import Any
from pydantic import BaseModel, Field, field_validator, ValidationInfo, ValidationError, AliasChoices
from src.core.schemas import DocumentGroup
from src.llm.llm import LLMFailureError
from src.processing.routing.config import (
    CATEGORY_TO_FOLDERS, 
    SINGLE_MATCH, 
    DIRECT_ROUTED_CATEGORIES, 
    FORM_CATEGORIES, 
    FORM_FOLDERS, 
    LETTER_CATEGORIES, 
    LETTER_FOLDERS,
    FOLDER_ROUTING
)

logger = logging.getLogger(f"file_organizer.{__name__}")

from src.core.exceptions import PipelineHaltError

class RoutingValidationError(PipelineHaltError):
    """Exception raised when LLM fails to provide a valid folder after multiple attempts."""
    pass

class RoutingResponse(BaseModel):
    reason: str = Field(
        validation_alias=AliasChoices('reason', 'reasoning'),
        description="Explanation of why this folder was selected"
    )
    selected_folder: str = Field(description="The exact name of the selected folder from the allowed list")

    @field_validator('selected_folder')
    @classmethod
    def validate_folder(cls, v: str, info: ValidationInfo) -> str:
        allowed = info.context.get('allowed_folders', []) if info.context else []
        if v not in allowed:
            raise ValueError(f"Selected folder '{v}' is not in the allowed list: {allowed}")
        return v

def double_check_others(group: DocumentGroup, llm_client: Any) -> str:
    """Double-check routing for documents categorized as others or hitting the escape hatch.
    
    Implements a two-step verification to reduce 'Miscellaneous' dumping and handle hallucinations.
    """
    all_folders = list(FOLDER_ROUTING.keys())
    folder_meanings = "\n".join([f"- {f}: {FOLDER_ROUTING[f]['desc']}" for f in all_folders])
    
    # Step 1: Initial pick from all folders
    prompt = f"""You are an expert document routing assistant.
The document was initially categorized as 'Miscellaneous' or 'Other'. 
Please re-evaluate if it fits into any of the following specific folders.

Allowed Folders:
{"\n".join(f"- {f}" for f in all_folders)}

Folder meanings:
{folder_meanings}

Document Summary: {group.brief_arabic_title or 'N/A'}
Reasoning: {group.reason or 'N/A'}

Respond only with a valid JSON matching the requested schema.
"""
    try:
        result = llm_client.generate_content(
            contents=[prompt],
            response_schema=RoutingResponse,
            validation_context={'allowed_folders': all_folders}
        )
        if not result:
            return "رسائل متنوعة"
            
        initial_pick = result.selected_folder
        if initial_pick == "رسائل متنوعة":
            logger.info("Double-check Step 1: LLM confirmed 'رسائل متنوعة'.")
            return "رسائل متنوعة"
            
        # Step 2: Confirmation call if a specific folder was picked
        logger.info(f"Double-check Step 1: LLM suggested '{initial_pick}'. Confirming...")
        
        confirm_prompt = f"""You previously selected '{initial_pick}' for this document.
Are you sure this is the best fit, or should it be 'رسائل متنوعة' (Miscellaneous Letters)?

Document Summary: {group.brief_arabic_title or 'N/A'}

Allowed Folders for this confirmation:
- {initial_pick}
- رسائل متنوعة

Respond only with a valid JSON.
"""
        confirm_result = llm_client.generate_content(
            contents=[confirm_prompt],
            response_schema=RoutingResponse,
            validation_context={'allowed_folders': [initial_pick, "رسائل متنوعة"]}
        )
        
        if not confirm_result:
            logger.warning("Double-check Step 2: Confirmation call returned None. Falling back to 'رسائل متنوعة'.")
            return "رسائل متنوعة"
            
        final_pick = confirm_result.selected_folder
        
        if final_pick == initial_pick:
            logger.info(f"Double-check Step 2: LLM confirmed '{initial_pick}'.")
            return initial_pick
        elif final_pick == "رسائل متنوعة":
            logger.info("Double-check Step 2: LLM changed mind to 'رسائل متنوعة'.")
            return "رسائل متنوعة"
        else:
            logger.warning(f"Double-check Step 2: LLM returned unexpected value '{final_pick}'. Falling back to 'رسائل متنوعة'.")
            return "رسائل متنوعة"
            
    except Exception as e:
        logger.error(f"Error during double-check others: {e}. Falling back to 'رسائل متنوعة'.")
        return "رسائل متنوعة"

def route_document(group: DocumentGroup, llm_client: Any) -> tuple[str, bool]:
    """Route a document group to the appropriate folder.
    
    Args:
        group: The document group to route.
        llm_client: The LLM client to use for multi-match resolution.
        
    Returns:
        tuple[str, bool]: (folder_name, is_direct_routed)
    """
    category = group.category.lower() if group.category else "unknown"
    
    # Trigger double-check for others immediately
    if category in ("others", "other_letters"):
        logger.info(f"Category '{category}' detected for pages {group.start_page}-{group.end_page}. Triggering double-check flow.")
        folder = double_check_others(group, llm_client)
        return folder, False

    DIRECT_ROUTING_MAP = {
        "contract": "عقود",
        "id_cards": "بيانات شخصية",
        "utility_bills": "كهرباء وماء",
        "pictures": "صور ومعاينات"
    }

    if category in DIRECT_ROUTING_MAP:
        folder = DIRECT_ROUTING_MAP[category]
        return folder, True
        
    # --- Constrained Prompting Logic ---
    if category == "forms":
        allowed_folders = list(FORM_FOLDERS)
    elif category == "letters":
        allowed_folders = list(LETTER_FOLDERS)
    else:
        logger.error(f"Unknown category '{category}'. Routing cannot proceed deterministically.")
        allowed_folders = []
    
    if not allowed_folders:
        logger.error(f"Category '{category}' has no mapping. Routing cannot proceed.")
        raise RoutingValidationError(f"Category '{category}' has no mapping. Routing cannot proceed.")
        
    # Escape hatch
    ESCAPE_HATCH = "None of the above"
    if ESCAPE_HATCH not in allowed_folders:
        allowed_folders.append(ESCAPE_HATCH)
        
    # Generate folder meanings from FOLDER_ROUTING for the prompt
    folder_meanings = []
    for folder in allowed_folders:
        if folder == ESCAPE_HATCH:
            folder_meanings.append(f"- {ESCAPE_HATCH}: Use this if the document does not fit any of the other options")
        elif folder in FOLDER_ROUTING:
            folder_meanings.append(f"- {folder}: {FOLDER_ROUTING[folder]['desc']}")
        else:
            folder_meanings.append(f"- {folder}: Document related to {folder}")
            
    # Multi-match routing via LLM
    prompt_template = """You are an expert document routing assistant.
Your task is to assign a document to the most appropriate folder based on its summary, and explain why the document fits into the selected folder based on the summary.

Allowed Folders for this document type:
{allowed_folders}

Folder meanings:
{folder_meanings}

Respond only with a valid JSON matching the requested schema. The selected_folder MUST be exactly one of the allowed folders.
"""
    
    formatted_prompt = prompt_template.format(
        allowed_folders="\n".join(f"- {f}" for f in allowed_folders),
        folder_meanings="\n".join(folder_meanings)
    )
    
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
            
            # Handle Escape Hatch
            if selected == ESCAPE_HATCH:
                logger.info(f"Document (pages {group.start_page}-{group.end_page}) routed to escape hatch '{ESCAPE_HATCH}'. Triggering double-check flow.")
                selected = double_check_others(group, llm_client)
                reason = "Routed via escape hatch -> Double-check"
            
            logger.info(f"Routed category '{category}' (pages {group.start_page}-{group.end_page}) to '{selected}'. Reason: {reason}")
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
