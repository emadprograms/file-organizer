"""Core grouping logic."""
import logging
from typing import Any
from src.core.schemas import DocumentGroup, GroupingResponse
from src.llm.llm import LLMFailureError
from src.processing.grouping.utils import verify_groups, merge_chunks

log = logging.getLogger(__name__)

GROUPING_PROMPT = """You are an expert Arabic document analyst.
Your task is to identify logical multi-page document boundaries within a chunk of pages.

CRITICAL RULES:
1. Boundaries ONLY on subject/content shift. DO NOT split on date changes or sender changes.
2. Every page MUST be part of exactly one group. No gaps, no overlaps.
3. The first group must start at the first page of the chunk.
4. The last group must end at the last page of the chunk.
5. You MUST provide a "reason" string for every group explaining why you grouped these pages together, based on what you saw and didn't see.

FEW-SHOT EXAMPLES:

Example 1 (Date change without boundary):
Pages:
- Page 5: Letter to Ministry requesting maintenance on roof. Date: 2023-01-05
- Page 6: Reply from Ministry approving maintenance on roof. Date: 2023-02-10
Expected output: These pages belong to the SAME document group because the subject (roof maintenance) is the same, despite the date and sender changing.

Example 2 (Subject shift resulting in boundary):
Pages:
- Page 8: EWA Utility bill for electricity.
- Page 9: Letter regarding a completely separate housing allocation request.
Expected output: These pages belong to DIFFERENT document groups because the subject shifted from a utility bill to a housing allocation. Boundary between Page 8 and 9.

Identify the document groups and provide a brief Arabic title for each group.
"""

def _process_chunk(pages: list[Any], current_page_index: int, end_index: int, llm_client: Any) -> list[DocumentGroup]:
    chunk_pages = pages[current_page_index:end_index]
    pages_text = "\n".join([f"Page {current_page_index + i}: {getattr(p, 'content_explanation', '')}" for i, p in enumerate(chunk_pages)])
    prompt = f"{GROUPING_PROMPT}\n\nChunk range: Page {current_page_index} to Page {end_index - 1}\n\nPages Data:\n{pages_text}"
    
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
            log.warning("Tenant could not be resolved for group. Falling back to Unassigned.")
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

def process_with_shrink(pages: list[Any], llm_client: Any) -> list[DocumentGroup]:
    """Process pages to detect document boundaries, shrinking chunk size on failures."""
    if not pages:
        return []

    CHUNK_SIZES = [10, 5, 3]
    MAX_CONSECUTIVE_FAILURES = 5
    MAX_TOTAL_FAILURES = 10

    consecutive_failures = 0
    total_failures = 0
    chunk_size_idx = 0
    
    current_page_index = 0
    final_groups: list[DocumentGroup] = []
    
    while current_page_index < len(pages):
        if total_failures >= MAX_TOTAL_FAILURES:
            raise RuntimeError("Hard fail: 10 total failures in grouping boundary detection.")
            
        chunk_size = CHUNK_SIZES[chunk_size_idx]
        end_index = min(current_page_index + chunk_size, len(pages))
        
        try:
            chunk_groups = _process_chunk(pages, current_page_index, end_index, llm_client)
            
            if final_groups and current_page_index > 0:
                overlap_original_idx = getattr(pages[current_page_index], "original_index", current_page_index)
                final_groups = merge_chunks(final_groups, chunk_groups, overlap_original_idx)
            else:
                final_groups.extend(chunk_groups)
                
            overlap = 1 if end_index < len(pages) else 0
            current_page_index = end_index - overlap
            consecutive_failures = 0
            
        except ValueError as e:
            consecutive_failures += 1
            total_failures += 1
            log.warning(f"Validation Error: {e}")
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                chunk_size_idx = min(chunk_size_idx + 1, len(CHUNK_SIZES) - 1)
                consecutive_failures = 0
                log.warning(f"Shrinking chunk size to {CHUNK_SIZES[chunk_size_idx]}")
        except LLMFailureError:
            raise
        except Exception as e:
            error_str = str(e).lower()
            if isinstance(e, (RuntimeError, TimeoutError)) or "500" in error_str or "503" in error_str or "servererror" in error_str or "llm routing failed" in error_str:
                consecutive_failures += 1
                total_failures += 1
                log.warning(f"Server Error: {e}")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    chunk_size_idx = min(chunk_size_idx + 1, len(CHUNK_SIZES) - 1)
                    consecutive_failures = 0
                    log.warning(f"Shrinking chunk size to {CHUNK_SIZES[chunk_size_idx]}")
            else:
                raise e
    
    from src.logger import log_decision_trace
    try:
        payload_groups = [g.model_dump() if hasattr(g, "model_dump") else g.dict() for g in final_groups]
    except Exception:
        payload_groups = []
        
    log_decision_trace("grouping", {"final_groups": payload_groups})
    log.info(f"Grouping complete. Identified {len(final_groups)} groups.")
    return final_groups
