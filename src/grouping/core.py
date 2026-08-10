"""Core grouping logic."""
import logging
from typing import Any, Optional
from src.core.schemas import DocumentGroup, GroupingResponse
from src.core.exceptions import ProviderRotationExhaustedError, GracefulHaltException, PipelineHaltError
from src.llm.llm import LLMFailureError
from src.grouping.utils import verify_groups, merge_chunks
from src.grouping.config import MAINTENANCE_PROMPT, STRICT_ADMIN_PROMPT, OTHER_PROMPT
from src.grouping.state import GroupingStateManager, GroupingState

logger = logging.getLogger(f"file_organizer.{__name__}")

def _process_chunk(
    pages: list[Any], 
    current_page_index: int, 
    end_index: int, 
    llm_client: Any, 
    prompt_template: str, 
    content_field: str = "content_explanation", 
    model: str | None = None
) -> list[DocumentGroup]:
    """Process a chunk of pages using the LLM to identify document boundaries.

    Args:
        pages (list[Any]): The complete list of pages being processed.
        current_page_index (int): The starting index of the chunk within the pages list.
        end_index (int): The exclusive ending index of the chunk.
        llm_client (Any): The LLM client used for generating boundary decisions.
        prompt_template (str): The prompt template to use for the LLM call.
        content_field (str): The field on the page object to extract text from (default: "content_explanation").
        model (str | None): Optional specific LLM model to use for the call.

    Returns:
        list[DocumentGroup]: A list of DocumentGroup objects representing the identified documents within the chunk.
    """
    chunk_pages = pages[current_page_index:end_index]
    
    page_descriptions = []
    for i, p in enumerate(chunk_pages):
        if content_field == "dynamic":
            cat = getattr(p, 'category', '')
            if cat == "letters" and getattr(p, "subject", ""):
                main_text = getattr(p, "subject")
                context = getattr(p, 'content_explanation', '')
                text = f"Subject: {main_text}\nContext: {context}" if context else main_text
            else:
                text = getattr(p, 'content_explanation', '')
        else:
            main_text = getattr(p, content_field, getattr(p, 'content_explanation', ''))
            if content_field == "subject":
                context = getattr(p, 'content_explanation', '')
                text = f"Subject: {main_text}\nContext: {context}" if context else main_text
            else:
                text = main_text
                
        fine_cat = getattr(p, 'fine_category', None)
        fine_cat_reason = getattr(p, 'fine_category_reason', None)
        if fine_cat:
            text += f"\nFine Category: {fine_cat}"
            if fine_cat_reason:
                text += f"\nReason: {fine_cat_reason}"
                
        page_descriptions.append(f"Page {current_page_index + i}: {text}")
        
    pages_text = "\n".join(page_descriptions)
    prompt = f"{prompt_template}\n\nChunk range: Page {current_page_index} to Page {end_index - 1}\n\nPages Data:\n{pages_text}"
    
    response = llm_client.generate_content(
        contents=[prompt],
        response_schema=GroupingResponse,
        is_boundary_call=True,
        model=model
    )
    
    verify_groups(response.groups, current_page_index, end_index)
    
    chunk_groups = []
    for g in response.groups:
        g_pages = pages[g.start_page : g.end_page + 1]
        primary_tenant = getattr(g_pages[0], "canonical_tenant", "Unassigned")
        if primary_tenant == "Unassigned":
            logger.warning("Tenant could not be resolved for group. Falling back to Unassigned.")
        category = getattr(g_pages[0], "category", "UNKNOWN")
        dates = []
        for p in g_pages:
            d = getattr(p, "resolved_date", getattr(p, "date", None))
            if d and d != "NONE":
                dates.append(d)
        
        start_page_original = getattr(g_pages[0], "original_index", g.start_page)
        end_page_original = getattr(g_pages[-1], "original_index", g.end_page)
        
        doc_group = DocumentGroup(
            start_page=start_page_original,
            end_page=end_page_original,
            primary_tenant=primary_tenant,
            category=category,
            dates=dates,
            reason=g.reason,
            brief_arabic_title=g.brief_arabic_title
        )
        chunk_groups.append(doc_group)
    return chunk_groups

def process_with_shrink(
    pages: list[Any], 
    llm_client: Any, 
    state_manager: Any | None = None
) -> list[DocumentGroup]:
    """Process pages to detect document boundaries."""
    if not pages:
        return []

    def get_admin_cat(p):
        fc = getattr(p, 'fine_category', getattr(p, 'category', ''))
        return fc.split('-')[0] if '-' in fc else fc

    def is_maintenance(p):
        prefix = get_admin_cat(p)
        return prefix in ['10', '11', '04']

    blocks = []
    current_block = [pages[0]]
    for i in range(1, len(pages)):
        p1 = pages[i-1]
        p2 = pages[i]
        
        p1_maint = is_maintenance(p1)
        p2_maint = is_maintenance(p2)
        
        p1_prefix = get_admin_cat(p1)
        p2_prefix = get_admin_cat(p2)
        
        is_boundary = False
        if p1_maint != p2_maint:
            is_boundary = True
        elif not p1_maint and not p2_maint:
            if p1_prefix != p2_prefix:
                is_boundary = True
                
        if is_boundary:
            blocks.append(current_block)
            current_block = [p2]
        else:
            current_block.append(p2)
    if current_block:
        blocks.append(current_block)

    final_groups: list[DocumentGroup] = []
    
    for block in blocks:
        p1 = block[0]
        category = getattr(p1, 'category', 'unknown').lower()
        
        if is_maintenance(p1) or get_admin_cat(p1) == '05':
            start_page = getattr(block[0], "original_index", 0)
            end_page = getattr(block[-1], "original_index", len(block) - 1)
            primary_tenant = getattr(block[0], "canonical_tenant", "Unassigned")
            dates = []
            for p in block:
                d = getattr(p, "resolved_date", getattr(p, "date", None))
                if d and d != "NONE":
                    dates.append(d)
            reason_text = "Deterministic grouping: Maintenance Set." if is_maintenance(p1) else "Deterministic grouping: Contract."
            final_groups.append(DocumentGroup(
                start_page=start_page,
                end_page=end_page,
                primary_tenant=primary_tenant,
                category=category,
                dates=dates,
                reason=reason_text,
                brief_arabic_title=None
            ))
        elif category == "utility_bills":
            for i, page in enumerate(block):
                d = getattr(page, "resolved_date", getattr(page, "date", None))
                dates = [d] if d and d != "NONE" else []
                final_groups.append(DocumentGroup(
                    start_page=getattr(page, "original_index", i),
                    end_page=getattr(page, "original_index", i),
                    primary_tenant=getattr(page, "canonical_tenant", "Unassigned"),
                    category=category,
                    dates=dates,
                    reason="Deterministic bypass: Each utility bill page is a separate document.",
                    brief_arabic_title=None
                ))
        else:
            content_field = "dynamic"
            current_page_index = 0
            chunk_size_idx = 0
            current_chunk_failure_count = 0
            total_failures = 0
            fallback_model_idx = -1
            FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash"]
            
            block_groups = []
            while current_page_index < len(block):
                if total_failures >= 30:
                    raise RuntimeError("Hard fail: 30 total failures in grouping boundary detection.")
                
                has_maintenance = any(is_maintenance(p) for p in block[current_page_index:min(current_page_index + 22, len(block))])
                CHUNK_SIZES = [22, 11, 5] if has_maintenance else [4, 3, 2]
                prompt_template = STRICT_ADMIN_PROMPT
                    
                chunk_size = CHUNK_SIZES[chunk_size_idx if chunk_size_idx < len(CHUNK_SIZES) else -1]
                end_index = min(current_page_index + chunk_size, len(block))
                
                try:
                    actual_chunk_size = end_index - current_page_index
                    start_orig = getattr(block[current_page_index], "original_index", current_page_index)
                    end_orig = getattr(block[end_index - 1], "original_index", end_index - 1)
                    
                    current_model = FALLBACK_MODELS[fallback_model_idx] if fallback_model_idx >= 0 else None
                    model_log = f" [Model: {current_model}]" if current_model else ""
                    logger.info(f"Processing fuzzy chunk for category '{category}'. Chunk size: {actual_chunk_size}. Pages: [{start_orig}-{end_orig}]{model_log}")
                    
                    chunk_groups = _process_chunk(
                        block, 
                        current_page_index, 
                        end_index, 
                        llm_client, 
                        prompt_template, 
                        content_field,
                        model=current_model
                    )
                    
                    if block_groups and current_page_index > 0:
                        overlap_original_idx = getattr(block[current_page_index], "original_index", current_page_index)
                        block_groups = merge_chunks(block_groups, chunk_groups, overlap_original_idx)
                    else:
                        block_groups.extend(chunk_groups)
                        
                    group_details = [f"Group {idx+1} (pages {g.start_page}-{g.end_page})" for idx, g in enumerate(chunk_groups)]
                    logger.info(f"Grouping complete for chunk. Identified {len(chunk_groups)} groups: {', '.join(group_details)}")
                        
                    overlap = 1 if (end_index < len(block) and actual_chunk_size > 1) else 0
                    current_page_index = end_index - overlap
                    
                    chunk_size_idx = 0
                    current_chunk_failure_count = 0
                    fallback_model_idx = -1
                    
                except (ProviderRotationExhaustedError, PipelineHaltError) as e:
                    logger.error(f"Critical LLM failure during grouping. Halting pipeline: {e}")
                    raise
                except (ValueError, LLMFailureError) as e:
                    total_failures += 1
                    current_chunk_failure_count += 1
                    logger.warning(f"Processing Error (ValueError/LLMFailureError): {e}")
                    
                    error_str = str(e).lower()
                    is_fatal_error = any(term in error_str for term in ["500", "503", "parse", "parsing", "token", "8000", "too large"])

                    threshold = 1 if is_fatal_error else (3 if CHUNK_SIZES[chunk_size_idx] <= 2 else 1)
                        
                    if current_chunk_failure_count >= threshold:
                        if chunk_size_idx < len(CHUNK_SIZES) - 1:
                            while chunk_size_idx < len(CHUNK_SIZES) - 1:
                                chunk_size_idx += 1
                                if CHUNK_SIZES[chunk_size_idx] < actual_chunk_size:
                                    break
                            current_chunk_failure_count = 0
                            logger.warning(f"Shrinking chunk size due to error to {CHUNK_SIZES[chunk_size_idx]}")
                        else:
                            if fallback_model_idx < len(FALLBACK_MODELS) - 1:
                                fallback_model_idx += 1
                                current_chunk_failure_count = 0
                                logger.warning(f"Error threshold reached. Falling back to model: {FALLBACK_MODELS[fallback_model_idx]}")
                            else:
                                raise GracefulHaltException(f"Grouping failed at minimum chunk size {CHUNK_SIZES[-1]} due to repeated processing errors. All fallbacks exhausted. Halting gracefully.") from e
                    else:
                        logger.info(f"Error {current_chunk_failure_count}/{threshold} at size {CHUNK_SIZES[chunk_size_idx]}. Retrying same size.")
                    continue
                except Exception as e:
                    raise e
            final_groups.extend(block_groups)

    from src.utils.logger import log_decision_trace
    try:
        payload_groups = [g.model_dump() if hasattr(g, "model_dump") else g.dict() for g in final_groups]
    except Exception:
        payload_groups = []
        
    log_decision_trace("grouping", {"final_groups": payload_groups})
    logger.info(f"Run complete. Total groups identified: {len(final_groups)}")
    return final_groups
