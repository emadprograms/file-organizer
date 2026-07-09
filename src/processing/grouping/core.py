"""Core grouping logic."""
import logging
from typing import Any, Optional
from src.core.schemas import DocumentGroup, GroupingResponse
from src.core.exceptions import ProviderRotationExhaustedError, GracefulHaltException
from src.llm.llm import LLMFailureError
from src.processing.grouping.utils import verify_groups, merge_chunks
from src.processing.grouping.config import LETTER_PROMPT, FORM_PROMPT, OTHER_PROMPT
from src.processing.grouping.state import GroupingStateManager, GroupingState

logger = logging.getLogger(f"file_organizer.{__name__}")

def _process_chunk(pages: list[Any], current_page_index: int, end_index: int, llm_client: Any, prompt_template: str, content_field: str = "content_explanation") -> list[DocumentGroup]:
    chunk_pages = pages[current_page_index:end_index]
    
    page_descriptions = []
    for i, p in enumerate(chunk_pages):
        main_text = getattr(p, content_field, getattr(p, 'content_explanation', ''))
        if content_field == "subject":
            context = getattr(p, 'content_explanation', '')
            text = f"Subject: {main_text}\nContext: {context}" if context else main_text
        else:
            text = main_text
        page_descriptions.append(f"Page {current_page_index + i}: {text}")
        
    pages_text = "\n".join(page_descriptions)
    prompt = f"{prompt_template}\n\nChunk range: Page {current_page_index} to Page {end_index - 1}\n\nPages Data:\n{pages_text}"
    
    response = llm_client.generate_content(
        contents=[prompt],
        response_schema=GroupingResponse,
        is_boundary_call=True
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

def process_with_shrink(pages: list[Any], llm_client: Any, state_manager: Optional[GroupingStateManager] = None) -> list[DocumentGroup]:
    """Process pages to detect document boundaries, shrinking chunk size on failures."""
    if not pages:
        return []

    category = getattr(pages[0], 'category', 'unknown').lower()
    final_groups: list[DocumentGroup] = []

    # Deterministic Bypass Paths
    if category in ["contract", "id_cards"]:
        start_page = getattr(pages[0], "original_index", 0)
        end_page = getattr(pages[-1], "original_index", len(pages) - 1)
        primary_tenant = getattr(pages[0], "canonical_tenant", "Unassigned")
        dates = []
        for p in pages:
            d = getattr(p, "resolved_date", getattr(p, "date", None))
            if d and d != "NONE":
                dates.append(d)
        
        final_groups.append(DocumentGroup(
            start_page=start_page,
            end_page=end_page,
            primary_tenant=primary_tenant,
            category=category,
            dates=dates,
            reason="Deterministic bypass: Category identified as cohesive document.",
            brief_arabic_title=None
        ))
    elif category == "utility_bills":
        for i, page in enumerate(pages):
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
        # Dynamic Routing Paths
        if category == "others":
            CHUNK_SIZES = [2]
            prompt_template = OTHER_PROMPT
            content_field = "content_explanation"
        elif category == "letters":
            CHUNK_SIZES = [4, 3, 2]
            prompt_template = LETTER_PROMPT
            content_field = "subject"
        else:
            CHUNK_SIZES = [4, 3, 2]
            prompt_template = FORM_PROMPT
            content_field = "content_explanation"

        # State Initialization
        if state_manager:
            state = state_manager.load_state()
            current_page_index = state.current_page_index
            chunk_size_idx = state.chunk_size_index
            current_chunk_failure_count = state.current_chunk_failure_count
            total_failures = state.failure_count
            for g_dict in state.processed_groups:
                final_groups.append(DocumentGroup(**g_dict))
        else:
            current_page_index = 0
            chunk_size_idx = 0
            current_chunk_failure_count = 0
            total_failures = 0
        
        while current_page_index < len(pages):
            if total_failures >= 10:
                raise RuntimeError("Hard fail: 10 total failures in grouping boundary detection.")
                
            chunk_size = CHUNK_SIZES[chunk_size_idx]
            end_index = min(current_page_index + chunk_size, len(pages))
            
            try:
                chunk_groups = _process_chunk(pages, current_page_index, end_index, llm_client, prompt_template, content_field)
                
                if final_groups and current_page_index > 0:
                    overlap_original_idx = getattr(pages[current_page_index], "original_index", current_page_index)
                    final_groups = merge_chunks(final_groups, chunk_groups, overlap_original_idx)
                else:
                    final_groups.extend(chunk_groups)
                    
                overlap = 1 if end_index < len(pages) else 0
                current_page_index = end_index - overlap
                
                # SUCCESS: Reset chunk size index and failure counters
                chunk_size_idx = 0
                current_chunk_failure_count = 0
                
                if state_manager:
                    state_manager.save_state(GroupingState(
                        current_page_index=current_page_index,
                        chunk_size_index=chunk_size_idx,
                        current_chunk_failure_count=current_chunk_failure_count,
                        failure_count=total_failures,
                        processed_groups=[g.model_dump() for g in final_groups]
                    ))
                
            except ProviderRotationExhaustedError as e:
                total_failures += 1
                current_chunk_failure_count += 1
                logger.warning(f"Rotation failure at size {CHUNK_SIZES[chunk_size_idx]}: {e}")
                
                threshold = 3 if chunk_size_idx == 0 else 1
                if current_chunk_failure_count >= threshold:
                    if chunk_size_idx < len(CHUNK_SIZES) - 1:
                        chunk_size_idx += 1
                        current_chunk_failure_count = 0
                        logger.warning(f"Threshold reached. Shrinking chunk size to {CHUNK_SIZES[chunk_size_idx]}")
                    else:
                        # GRACEFUL HALT: minimum size failed
                        if state_manager:
                            state_manager.save_state(GroupingState(
                                current_page_index=current_page_index,
                                chunk_size_index=chunk_size_idx,
                                current_chunk_failure_count=current_chunk_failure_count,
                                failure_count=total_failures,
                                processed_groups=[g.model_dump() for g in final_groups]
                            ))
                        raise GracefulHaltException(f"Grouping failed at minimum chunk size {CHUNK_SIZES[-1]}. Halting gracefully.") from e
                else:
                    logger.info(f"Failure {current_chunk_failure_count}/{threshold} at size {CHUNK_SIZES[chunk_size_idx]}. Retrying same size.")
            
            except (ValueError, LLMFailureError) as e:
                total_failures += 1
                current_chunk_failure_count += 1
                logger.warning(f"Processing Error (not rotation exhausted): {e}")
                
                threshold = 3 if chunk_size_idx == 0 else 1
                if current_chunk_failure_count >= threshold:
                    if chunk_size_idx < len(CHUNK_SIZES) - 1:
                        chunk_size_idx += 1
                        current_chunk_failure_count = 0
                        logger.warning(f"Shrinking chunk size due to error to {CHUNK_SIZES[chunk_size_idx]}")
                continue
            except Exception as e:
                raise e
    
    from src.logger import log_decision_trace
    try:
        payload_groups = [g.model_dump() if hasattr(g, "model_dump") else g.dict() for g in final_groups]
    except Exception:
        payload_groups = []
        
    log_decision_trace("grouping", {"final_groups": payload_groups})
    logger.info(f"Grouping complete. Identified {len(final_groups)} groups.")
    return final_groups
