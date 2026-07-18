"""Core grouping logic."""
import logging
from typing import Any, Optional
from src.core.schemas import DocumentGroup, GroupingResponse
from src.core.exceptions import ProviderRotationExhaustedError, GracefulHaltException
from src.llm.llm import LLMFailureError
from src.grouping.utils import verify_groups, merge_chunks
from src.grouping.config import LETTER_PROMPT, FORM_PROMPT, OTHER_PROMPT
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
    """Process pages to detect document boundaries, shrinking chunk size on failures.

    Applies deterministic grouping for certain categories and dynamically shrinks 
    LLM chunk sizes if boundaries cannot be resolved or rate limits are hit.

    Args:
        pages (list[Any]): The pages to group.
        llm_client (Any): The LLM client instance.
        state_manager (Any | None): Optional manager to track and persist progress state.

    Returns:
        list[DocumentGroup]: The finalized list of document groups.

    Raises:
        RuntimeError: If the grouping fails repeatedly beyond the hard threshold limit.
        GracefulHaltException: If all fallback models and chunk shrinking fail.
    """
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
            
        fallback_model_idx = -1
        FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3-flash", "gemini-2.5-flash"]
        
        while current_page_index < len(pages):
            if total_failures >= 20:
                raise RuntimeError("Hard fail: 20 total failures in grouping boundary detection.")
                
            chunk_size = CHUNK_SIZES[chunk_size_idx]
            end_index = min(current_page_index + chunk_size, len(pages))
            
            try:
                actual_chunk_size = end_index - current_page_index
                start_orig = getattr(pages[current_page_index], "original_index", current_page_index)
                end_orig = getattr(pages[end_index - 1], "original_index", end_index - 1)
                
                current_model = FALLBACK_MODELS[fallback_model_idx] if fallback_model_idx >= 0 else None
                model_log = f" [Model: {current_model}]" if current_model else ""
                logger.info(f"Processing chunk for category '{category}'. Chunk size: {actual_chunk_size}. Pages: [{start_orig}-{end_orig}]{model_log}")
                
                chunk_groups = _process_chunk(
                    pages, 
                    current_page_index, 
                    end_index, 
                    llm_client, 
                    prompt_template, 
                    content_field,
                    model=current_model
                )
                
                if final_groups and current_page_index > 0:
                    overlap_original_idx = getattr(pages[current_page_index], "original_index", current_page_index)
                    final_groups = merge_chunks(final_groups, chunk_groups, overlap_original_idx)
                else:
                    final_groups.extend(chunk_groups)
                    
                group_details = [f"Group {idx+1} (pages {g.start_page}-{g.end_page})" for idx, g in enumerate(chunk_groups)]
                logger.info(f"Grouping complete for chunk. Identified {len(chunk_groups)} groups: {', '.join(group_details)}")
                    
                overlap = 1 if (end_index < len(pages) and actual_chunk_size > 1) else 0
                current_page_index = end_index - overlap
                
                # SUCCESS: Reset chunk size index and failure counters
                chunk_size_idx = 0
                current_chunk_failure_count = 0
                fallback_model_idx = -1
                
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
                
                if CHUNK_SIZES[chunk_size_idx] == 4:
                    threshold = 1
                elif CHUNK_SIZES[chunk_size_idx] == 3:
                    threshold = 1
                elif CHUNK_SIZES[chunk_size_idx] == 2:
                    threshold = 3
                else:
                    threshold = 1
                    
                if current_chunk_failure_count >= threshold:
                    if chunk_size_idx < len(CHUNK_SIZES) - 1:
                        while chunk_size_idx < len(CHUNK_SIZES) - 1:
                            chunk_size_idx += 1
                            if CHUNK_SIZES[chunk_size_idx] < actual_chunk_size:
                                break
                        current_chunk_failure_count = 0
                        logger.warning(f"Threshold reached. Shrinking chunk size to {CHUNK_SIZES[chunk_size_idx]}")
                    else:
                        # Minimum size failed, check fallback models
                        if fallback_model_idx < len(FALLBACK_MODELS) - 1:
                            fallback_model_idx += 1
                            current_chunk_failure_count = 0
                            logger.warning(f"Threshold reached. Falling back to model: {FALLBACK_MODELS[fallback_model_idx]}")
                        else:
                            # GRACEFUL HALT: all fallbacks exhausted
                            if state_manager:
                                state_manager.save_state(GroupingState(
                                    current_page_index=current_page_index,
                                    chunk_size_index=chunk_size_idx,
                                    current_chunk_failure_count=current_chunk_failure_count,
                                    failure_count=total_failures,
                                    processed_groups=[g.model_dump() for g in final_groups]
                                ))
                            raise GracefulHaltException(f"Grouping failed at minimum chunk size {CHUNK_SIZES[-1]} and all fallback models exhausted. Halting gracefully.") from e
                else:
                    logger.info(f"Failure {current_chunk_failure_count}/{threshold} at size {CHUNK_SIZES[chunk_size_idx]}. Retrying same size.")
            
            except (ValueError, LLMFailureError) as e:
                total_failures += 1
                current_chunk_failure_count += 1
                logger.warning(f"Processing Error (not rotation exhausted): {e}")
                
                error_str = str(e).lower()
                is_fatal_error = any(term in error_str for term in ["500", "503", "parse", "parsing", "token", "8000", "too large"])

                if CHUNK_SIZES[chunk_size_idx] == 4:
                    threshold = 1 if is_fatal_error else 1 # User requested 4 -> 3 immediately on failure
                elif CHUNK_SIZES[chunk_size_idx] == 3:
                    threshold = 1
                elif CHUNK_SIZES[chunk_size_idx] == 2:
                    threshold = 3
                else:
                    threshold = 1
                    
                if current_chunk_failure_count >= threshold:
                    if chunk_size_idx < len(CHUNK_SIZES) - 1:
                        while chunk_size_idx < len(CHUNK_SIZES) - 1:
                            chunk_size_idx += 1
                            if CHUNK_SIZES[chunk_size_idx] < actual_chunk_size:
                                break
                        current_chunk_failure_count = 0
                        logger.warning(f"Shrinking chunk size due to error to {CHUNK_SIZES[chunk_size_idx]}")
                    else:
                        # Minimum size failed, check fallback models
                        if fallback_model_idx < len(FALLBACK_MODELS) - 1:
                            fallback_model_idx += 1
                            current_chunk_failure_count = 0
                            logger.warning(f"Error threshold reached. Falling back to model: {FALLBACK_MODELS[fallback_model_idx]}")
                        else:
                            if state_manager:
                                state_manager.save_state(GroupingState(
                                    current_page_index=current_page_index,
                                    chunk_size_index=chunk_size_idx,
                                    current_chunk_failure_count=current_chunk_failure_count,
                                    failure_count=total_failures,
                                    processed_groups=[g.model_dump() for g in final_groups]
                                ))
                            raise GracefulHaltException(f"Grouping failed at minimum chunk size {CHUNK_SIZES[-1]} due to repeated processing errors. All fallbacks exhausted. Halting gracefully.") from e
                else:
                    logger.info(f"Error {current_chunk_failure_count}/{threshold} at size {CHUNK_SIZES[chunk_size_idx]}. Retrying same size.")
                continue
            except Exception as e:
                raise e
    
    from src.utils.logger import log_decision_trace
    try:
        payload_groups = [g.model_dump() if hasattr(g, "model_dump") else g.dict() for g in final_groups]
    except Exception:
        payload_groups = []
        
    log_decision_trace("grouping", {"final_groups": payload_groups})
    logger.info(f"Run complete for category '{category}'. Total groups identified: {len(final_groups)}")
    return final_groups
