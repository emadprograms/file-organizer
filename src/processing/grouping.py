from typing import Any
import logging
from src.core.schemas import GroupEntry, DocumentGroup, GroupingResponse
from src.core.config import GEMINI_MODEL

log = logging.getLogger(__name__)

GROUPING_PROMPT = """You are an expert Arabic document analyst.
Your task is to identify logical multi-page document boundaries within a chunk of pages.

CRITICAL RULES:
1. Boundaries ONLY on subject/content shift. DO NOT split on date changes or sender changes.
2. Every page MUST be part of exactly one group. No gaps, no overlaps.
3. The first group must start at the first page of the chunk.
4. The last group must end at the last page of the chunk.

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

def category_presplit(pages: list[Any]) -> list[list[Any]]:
    """
    Split a sequence of pages into contiguous runs of the same category.
    A new sublist is created every time `page.category` changes.
    """
    if not pages:
        return []
        
    runs = []
    current_run = [pages[0]]
    current_category = getattr(pages[0], "category", None)
    
    for page in pages[1:]:
        cat = getattr(page, "category", None)
        if cat == current_category:
            current_run.append(page)
        else:
            runs.append(current_run)
            current_run = [page]
            current_category = cat
            
    if current_run:
        runs.append(current_run)
        
    return runs

def verify_groups(groups: list[GroupEntry], chunk_start_idx: int, chunk_end_idx: int) -> bool:
    """
    Programmatic verification of LLM grouping output.
    Returns True if valid, raises ValueError if invalid.
    - No gaps
    - No overlaps
    - No invented pages (starts at chunk_start_idx, ends at chunk_end_idx - 1)
    """
    if not groups:
        raise ValueError("Groups list is empty")
        
    if groups[0].start_page != chunk_start_idx:
        raise ValueError(f"First group start_page ({groups[0].start_page}) does not match chunk_start_idx ({chunk_start_idx})")
        
    for i in range(len(groups) - 1):
        if groups[i].end_page + 1 != groups[i+1].start_page:
            raise ValueError(f"Gap or overlap detected between group {i} (ends {groups[i].end_page}) and group {i+1} (starts {groups[i+1].start_page})")
            
    if groups[-1].end_page != chunk_end_idx - 1:
        raise ValueError(f"Last group end_page ({groups[-1].end_page}) does not match chunk end boundary ({chunk_end_idx - 1})")
        
    return True

def merge_chunks(chunk1_groups: list[DocumentGroup], chunk2_groups: list[DocumentGroup], overlap_page_idx: int) -> list[DocumentGroup]:
    """
    Merge two lists of groups from adjacent chunks that share an overlap page.
    Trust Chunk 1's metadata for the merged group.
    """
    if not chunk1_groups or not chunk2_groups:
        return chunk1_groups + chunk2_groups
        
    last_g1 = chunk1_groups[-1]
    first_g2 = chunk2_groups[0]
    
    def contains_page(group: DocumentGroup, page_idx: int) -> bool:
        return group.start_page <= page_idx <= group.end_page

    if contains_page(last_g1, overlap_page_idx) and contains_page(first_g2, overlap_page_idx):
        merged_group = DocumentGroup(
            start_page=last_g1.start_page,
            end_page=max(last_g1.end_page, first_g2.end_page),
            primary_tenant=last_g1.primary_tenant,
            category=last_g1.category,
            dates=last_g1.dates,
            reason=last_g1.reason,
            brief_arabic_title=last_g1.brief_arabic_title,
            folder_path=last_g1.folder_path,
            is_direct_routed=last_g1.is_direct_routed
        )
        return chunk1_groups[:-1] + [merged_group] + chunk2_groups[1:]
        
    return chunk1_groups + chunk2_groups

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
        chunk_pages = pages[current_page_index:end_index]
        
        pages_text = "\\n".join([f"Page {current_page_index + i}: {getattr(p, 'content_explanation', '')}" for i, p in enumerate(chunk_pages)])
        prompt = f"{GROUPING_PROMPT}\\n\\nChunk range: Page {current_page_index} to Page {end_index - 1}\\n\\nPages Data:\\n{pages_text}"
        
        try:
            response = llm_client._route_llm_call(
                model=GEMINI_MODEL,
                contents=[prompt],
                response_schema=GroupingResponse,
                log_prefix="Grouping"
            )
            
            verify_groups(response.groups, current_page_index, end_index)
            
            chunk_groups = []
            for g in response.groups:
                g_pages = pages[g.start_page : g.end_page + 1]
                res = getattr(g_pages[0], "residents", [])
                primary_tenant = res[0] if res else "UNKNOWN"
                category = getattr(g_pages[0], "category", "UNKNOWN")
                dates = []
                for p in g_pages:
                    d = getattr(p, "date", None)
                    if d and d != "NONE":
                        dates.append(d)
                
                doc_group = DocumentGroup(
                    start_page=g.start_page,
                    end_page=g.end_page,
                    primary_tenant=primary_tenant,
                    category=category,
                    dates=dates,
                    reason=g.reason,
                    brief_arabic_title=g.brief_arabic_title
                )
                chunk_groups.append(doc_group)
                
            if final_groups and current_page_index > 0:
                final_groups = merge_chunks(final_groups, chunk_groups, current_page_index)
            else:
                final_groups.extend(chunk_groups)
                
            overlap = 1 if end_index < len(pages) else 0
            current_page_index = end_index - overlap
            consecutive_failures = 0
            
        except ValueError as e:
            # ValidationError
            consecutive_failures += 1
            total_failures += 1
            log.warning(f"Validation Error: {e}")
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                chunk_size_idx = min(chunk_size_idx + 1, len(CHUNK_SIZES) - 1)
                consecutive_failures = 0
                log.warning(f"Shrinking chunk size to {CHUNK_SIZES[chunk_size_idx]}")
        except Exception as e:
            # Treat 500 and other LLM errors (which llm_client raises if all retries fail) as failure
            # 429s are handled normally inside llm_client._route_llm_call (it sleeps and retries).
            # If a TimeoutError or other server error slips out, we treat it as failure here.
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
                # Other errors (e.g. 401, etc.) just raise
                raise e
    
    return final_groups

