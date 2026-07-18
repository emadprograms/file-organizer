"""Utility functions for grouping documents."""

import logging
from typing import Any
from src.core.schemas import GroupEntry, DocumentGroup

logger = logging.getLogger(f"file_organizer.{__name__}")

def category_presplit(pages: list[Any]) -> list[list[Any]]:
    """Split a sequence of pages into contiguous runs of the same category.

    A new sublist is created every time `page.category` changes.

    Args:
        pages (list[Any]): A list of extracted page objects.

    Returns:
        list[list[Any]]: A list of page chunks, where each chunk contains pages of the same category.
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
    """Verify LLM grouping output programmatically.

    Validates that there are no gaps or overlaps between groups, and that the 
    groups exactly cover the range [chunk_start_idx, chunk_end_idx - 1].

    Args:
        groups (list[GroupEntry]): The groups returned by the LLM.
        chunk_start_idx (int): The expected starting page index.
        chunk_end_idx (int): The expected exclusive ending page index.

    Returns:
        bool: True if valid.

    Raises:
        ValueError: If gaps, overlaps, or boundary mismatches are detected.
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

def merge_chunks(
    chunk1_groups: list[DocumentGroup], 
    chunk2_groups: list[DocumentGroup], 
    overlap_page_idx: int
) -> list[DocumentGroup]:
    """Merge two lists of groups from adjacent chunks that share an overlap page.

    Uses an 'Anchor Page' strategy: merging occurs only if the anchor page is 
    a consistent continuation in both chunks. If decisions conflict, it splits at the boundary.

    Args:
        chunk1_groups (list[DocumentGroup]): The groups identified in the first chunk.
        chunk2_groups (list[DocumentGroup]): The groups identified in the second chunk.
        overlap_page_idx (int): The original index of the page that is shared between chunks.

    Returns:
        list[DocumentGroup]: The merged list of document groups.
    """
    if not chunk1_groups or not chunk2_groups:
        return chunk1_groups + chunk2_groups
        
    def contains_page(group: DocumentGroup, page_idx: int) -> bool:
        return group.start_page <= page_idx <= group.end_page

    # Find the groups containing the anchor page
    group_prev = next((g for g in chunk1_groups if contains_page(g, overlap_page_idx)), None)
    group_curr = next((g for g in chunk2_groups if contains_page(g, overlap_page_idx)), None)
    
    if not group_prev or not group_curr:
        # This should not happen with proper overlap, but for safety:
        return chunk1_groups + chunk2_groups

    # Boundary Validation: Check if it's a continuation in both or a boundary in both.
    # Merge if they agree on the 'continuity' of the anchor page.
    # Continuation means: (starts before anchor) AND (ends after anchor).
    # We use a simplified logic: merge if they are both continuing or both boundaries.
    is_prev_continuing = group_prev.start_page < overlap_page_idx
    is_curr_continuing = group_curr.end_page > overlap_page_idx
    
    if is_prev_continuing == is_curr_continuing:
        # SUCCESS: They agree on the nature of the anchor page (both continuing or both single-page/boundary).
        merged_group = DocumentGroup(
            start_page=group_prev.start_page,
            end_page=max(group_prev.end_page, group_curr.end_page),
            primary_tenant=group_prev.primary_tenant,
            category=group_prev.category,
            dates=group_prev.dates,
            reason=group_prev.reason,
            brief_arabic_title=group_prev.brief_arabic_title,
            folder_path=group_prev.folder_path,
            is_direct_routed=group_prev.is_direct_routed
        )
        
        # Construct result: everything before group_prev, the merged group, everything after group_curr.
        prev_part = [g for g in chunk1_groups if g != group_prev]
        curr_part = [g for g in chunk2_groups if g != group_curr]
        return prev_part + [merged_group] + curr_part

    # CONFLICT: One sees it as a continuation, the other as a boundary.
    # Default to SPLIT: trust Chunk 2 for the start of the new segment.
    # Truncate Chunk 1's group to end just before the anchor page.
    truncated_prev = None
    if group_prev.start_page < overlap_page_idx:
        truncated_prev = DocumentGroup(
            **{**group_prev.model_dump(), "end_page": overlap_page_idx - 1}
        )
        
    prev_part = [g for g in chunk1_groups if g != group_prev]
    if truncated_prev:
        prev_part.append(truncated_prev)
    
    # To ensure chronological order, we sort the prev_part (since we appended)
    prev_part.sort(key=lambda x: x.start_page)
    
    return prev_part + chunk2_groups
