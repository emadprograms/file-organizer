import logging
from typing import Any, Literal
from pydantic import BaseModel, Field
from src.core.exceptions import PipelineHaltError
from src.llm.llm import LLMFailureError
from src.routing.config import FOLDER_PREFIXES, FOLDER_ROUTING
import os
import json
from src.utils.fs import atomic_write

logger = logging.getLogger(f"file_organizer.{__name__}")

# Create the literal for categories
category_names = []
for name, prefix in FOLDER_PREFIXES.items():
    category_names.append(f"{prefix}-{name}")

CategoryLiteral = Literal[tuple(category_names)]

class FineCategorizationResponse(BaseModel):
    reason: str = Field(description="Chain of thought reasoning for why this page belongs to the chosen category. Think step-by-step.")
    category: CategoryLiteral = Field(description="The final selected category.")

def process_fine_categorization(pages: list[Any], llm_client: Any, model: str | None = None, run_checkpoint_path: str | None = None) -> list[Any]:
    """Run fine-grained categorization on each page."""
    
    processed_indices = set()
    if run_checkpoint_path and os.path.exists(run_checkpoint_path):
        try:
            with open(run_checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
                processed_indices = set(checkpoint_data.get("processed_indices", []))
                for i, p_data in checkpoint_data.get("pages_data", {}).items():
                    idx = int(i)
                    if idx < len(pages):
                        pages[idx].fine_category = p_data.get("category")
                        pages[idx].fine_category_reason = p_data.get("reason")
            logger.info(f"Resuming fine categorization. Skipping {len(processed_indices)} processed pages.")
        except Exception as e:
            logger.warning(f"Failed to load fine categorization checkpoint: {e}")

    prompt_template = "Categorize this Arabic PDF page into one of the following specific routing categories:\n"
    for name, prefix in FOLDER_PREFIXES.items():
        desc = FOLDER_ROUTING.get(name, {}).get("desc", "")
        prompt_template += f"- {prefix}-{name}: {desc}\n"
        
    prompt_template += "\nRead the page carefully. You MUST output a `reason` field first to explain your thought process, followed by the `category` field with EXACTLY ONE of the above categories."
    prompt_template += "\n\nCRITICAL WARNING: The previous extraction pass may have incorrectly described an ID card as a 'form'. Do not be fooled! If the content clearly mentions a CPR, National ID, Smart Card, or Passport, you MUST classify it as `02-بيانات شخصية` (Personal Details), even if the text refers to it as a form or application."
    
    for idx, page in enumerate(pages):
        if idx in processed_indices:
            continue
            
        try:
            # We can use the content_explanation or subject + content
            text = getattr(page, 'content_explanation', '')
            if getattr(page, 'category', '') == 'letters' and getattr(page, 'subject', ''):
                text = f"Subject: {page.subject}\nContext: {text}"
                
            prompt = f"{prompt_template}\n\nPage text summary:\n{text}"
            
            logger.info(f"Fine categorizing page {idx}...")
            
            result = llm_client.generate_content(
                contents=[prompt],
                response_schema=FineCategorizationResponse,
                is_boundary_call=False,
                model=model
            )
            
            page.fine_category_reason = result.reason
            page.fine_category = result.category
            
            logger.info(f"Page {idx} categorized as {result.category}")
            
        except Exception as e:
            logger.error(f"Failed to fine-categorize page {idx}: {e}")
            page.fine_category_reason = f"Error: {e}"
            page.fine_category = "13-رسائل متنوعة" # Default fallback
            
        processed_indices.add(idx)
        
        # Save checkpoint
        if run_checkpoint_path:
            try:
                pages_data = {}
                for i in processed_indices:
                    pages_data[str(i)] = {
                        "category": pages[i].fine_category,
                        "reason": getattr(pages[i], "fine_category_reason", "")
                    }
                    
                os.makedirs(os.path.dirname(run_checkpoint_path), exist_ok=True)
                with atomic_write(run_checkpoint_path) as tmp_path:
                    with open(tmp_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            "processed_indices": list(processed_indices),
                            "pages_data": pages_data
                        }, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save fine categorization checkpoint: {e}")
            
    return pages
