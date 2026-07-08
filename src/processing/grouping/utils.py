"""Utility functions for grouping documents."""

import logging
from typing import Any
from src.core.schemas import GroupEntry, DocumentGroup

logger = logging.getLogger(f"file_organizer.{__name__}")

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
