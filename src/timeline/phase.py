import json
import logging
from pathlib import Path
from src.core.models import PageData, TenantTimeline
from src.timeline.dates import parse_flexible_date
from src.tenant_config.tenants import (
    cluster_names_fuzzily, 
    canonicalize_with_llm, 
    build_tenant_timelines
)
from src.llm.llm import LLMClient

logger = logging.getLogger(f"file_organizer.{__name__}")

def load_and_parse_json(json_path: Path) -> list[PageData]:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = []
    # If data is a list, iterate normally. If it's a dict (like the categorized report), iterate over sorted keys.
    if isinstance(data, dict):
        items = [data[k] for k in sorted(data.keys(), key=int)]
    else:
        items = data

    for i, item in enumerate(items):
        date_val = item.get("date")
        if date_val is not None:
            # normalize date
            try:
                date_val = parse_flexible_date(date_val)
                item["date"] = date_val
            except ValueError:
                item["date"] = None
        
        item["original_index"] = i
        pages.append(PageData(**item))

    if len(pages) != len(data):
        raise RuntimeError("Mismatch in parsed pages and source array length.")
    return pages

def infer_missing_dates(pages: list[PageData]) -> None:
    # Get all indices with a valid date
    valid_dates = [(p.original_index, p.date) for p in pages if p.date is not None]
    logger.info(f"Found {len(valid_dates)} pages with valid dates out of {len(pages)} total pages.")
    
    inferred_count = 0
    for page in pages:
        if page.date is not None:
            page.resolved_date = page.date
        else:
            if not valid_dates:
                continue # No valid dates at all, can't infer
            
            # Find the closest date
            closest = min(valid_dates, key=lambda x: (abs(x[0] - page.original_index), x[0]))
            page.resolved_date = closest[1]
            inferred_count += 1
            
    if inferred_count > 0:
        logger.info(f"Successfully inferred {inferred_count} missing dates using closest proximity matching.")

def assign_pages_to_tenants(pages: list[PageData], timelines: list[TenantTimeline]) -> None:
    for page in pages:
        if not page.resolved_date:
            page.canonical_tenant = "Unassigned (Unknown)"
            continue
            
        covering = []
        for t in timelines:
            if t.min_date <= page.resolved_date <= t.max_date:
                covering.append(t)
                
        if covering:
            covering.sort(key=lambda t: t.min_date)
            page.canonical_tenant = covering[0].canonical_name
        else:
            month_str = page.resolved_date[:7]
            page.canonical_tenant = f"Unassigned ({month_str})"

def process_cleaning_phase(json_path: Path, llm_client: LLMClient) -> list[PageData]:
    logger.info("==================================================")
    logger.info("           PHASE 1: DOCUMENT CLEANING             ")
    logger.info("==================================================")
    
    pages = load_and_parse_json(json_path)
    logger.info(f"Loaded {len(pages)} pages from {json_path}")
    
    logger.info("\n>>> DATE CLEANING WORKFLOW")
    infer_missing_dates(pages)
    
    logger.info("\n>>> NAME CLEANING WORKFLOW")
    anchor_categories = {"contract", "forms", "id_cards"}
    unique_anchors_seen = set()
    
    for page in pages:
        if page.expected_tenant_name:
            if page.category in anchor_categories:
                if page.expected_tenant_name not in unique_anchors_seen:
                    logger.info(f"Identified anchor document (category: {page.category}). Extracted name: '{page.expected_tenant_name}'")
                    unique_anchors_seen.add(page.expected_tenant_name)

    unique_names = {p.expected_tenant_name for p in pages if p.expected_tenant_name}
    logger.info(f"Total unique raw names extracted across all pages: {len(unique_names)}")
    
    fuzzy_map = cluster_names_fuzzily(unique_names)
    representatives = list(set(fuzzy_map.values()))
    logger.info(f"Clustered down to {len(representatives)} representative names via Fuzzy Matching.")
    
    logger.debug(f"Sending representative names to LLM: {representatives}")
    llm_map = canonicalize_with_llm(representatives, llm_client)
    for rep, canon in llm_map.items():
        logger.info(f"LLM normalized representative: '{rep}' -> '{canon}'")
    
    final_mapping = {}
    for raw, rep in fuzzy_map.items():
        final_mapping[raw] = llm_map.get(rep, rep)
        
    logger.info("\n>>> TIMELINE BUILDING")
    timelines = build_tenant_timelines(pages, final_mapping)
    
    logger.info("\n>>> FINAL OUTPUT FOR EACH DOCUMENT")
    assign_pages_to_tenants(pages, timelines)
    
    logger.info("ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ")
    logger.info("Γöé Page Γöé Date       Γöé Category   Γöé Tenant                                 Γöé")
    logger.info("Γö£ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö╝ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö╝ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö╝ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöñ")
    for page in pages:
        if page.canonical_tenant is None:
            raise RuntimeError("Page is missing canonical_tenant")
            
        date_str = page.resolved_date or "N/A"
        # We manually format the columns. The Tenant column gets 38 chars of space.
        logger.info(f"Γöé {page.original_index:02d}   Γöé {date_str:<10} Γöé {page.category:<10} Γöé {page.canonical_tenant:<38} Γöé")
    logger.info("ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö┤ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö┤ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö┤ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ")
    logger.info(f"Successfully mapped {len(pages)} pages to their respective canonical tenants.")
        
    logger.info("\n==================================================")
    logger.info("           CLEANING PHASE COMPLETE                ")
    logger.info("==================================================")
    return pages
