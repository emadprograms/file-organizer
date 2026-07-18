import json
import logging
import yaml
from pathlib import Path
from typing import Any
from src.core.models import PageData, TenantTimeline
from src.timeline.dates import parse_flexible_date
from src.grouping.name_matcher import cluster_names_fuzzily, canonicalize_with_llm
from src.timeline.timeline_builder import build_tenant_timelines
from src.llm.llm import LLMClient

logger = logging.getLogger(f"file_organizer.{__name__}")

def load_and_parse_json(json_path: Path) -> list[PageData]:
    """Load and parse page data from a JSON file.

    Reads the JSON file, normalizes the dates using flexible parsing, 
    and initializes PageData models.

    Args:
        json_path (Path): Path to the input JSON file.

    Returns:
        list[PageData]: The parsed list of PageData objects.

    Raises:
        RuntimeError: If the parsed pages count does not match the source data length.
    """
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
    """Infer missing dates on pages by applying the date from the nearest neighbor.

    Scans the pages, finds all valid dates, and assigns the closest date
    (by page index) to pages lacking a resolved date.

    Args:
        pages (list[PageData]): The list of pages to update in-place.
    """
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

def assign_pages_to_tenants(
    pages: list[PageData], 
    timelines: list[TenantTimeline], 
    final_mapping: dict[str, str]
) -> None:
    """Assign pages to canonical tenants based on extracted names and resolved dates.

    Matches the page to a tenant timeline. If the page has an expected name, it is 
    mapped via the canonical mapping. Otherwise, the date is used to find the corresponding 
    tenant timeline. If no timeline matches, falls back to the most recent tenant or marks unassigned.

    Args:
        pages (list[PageData]): The list of pages to update in-place.
        timelines (list[TenantTimeline]): The generated timelines for tenants.
        final_mapping (dict[str, str]): Mapping from raw names to canonical tenant names.
    """
    # Find the tenant marked as "present" or latest overall for D-11 fallback
    latest_tenant = None
    if timelines:
        # Sort by max_date to find the latest
        sorted_by_max = sorted(timelines, key=lambda t: t.max_date, reverse=True)
        latest_tenant = sorted_by_max[0].canonical_name

    valid_tenant_names = {t.canonical_name for t in timelines}

    for page in pages:
        if page.expected_tenant_name:
            mapped_name = final_mapping.get(page.expected_tenant_name)
            if mapped_name and mapped_name in valid_tenant_names:
                page.canonical_tenant = mapped_name
                continue
                
        if not page.resolved_date:
            if latest_tenant:
                page.canonical_tenant = latest_tenant
            else:
                page.canonical_tenant = "Unassigned (Unknown)"
            continue
            
        covering = []
        for t in timelines:
            if t.min_date <= page.resolved_date <= t.max_date:
                covering.append(t)
                
        if covering:
            # Sort by min_date descending to get the latest overlapping tenant (D-10)
            covering.sort(key=lambda t: t.min_date, reverse=True)
            page.canonical_tenant = covering[0].canonical_name
        else:
            month_str = page.resolved_date[:7]
            page.canonical_tenant = f"Unassigned ({month_str})"

def process_cleaning_phase(
    json_path: Path, 
    llm_client: LLMClient, 
    yaml_data: list[dict[str, Any]] | None
) -> tuple[list[PageData], list[dict[str, Any]] | None]:
    """Execute the data cleaning and timeline generation phase.

    Orchestrates the process of loading the page data, inferring dates, cleaning 
    and resolving tenant names, building chronological timelines, and finally 
    assigning each page to the correct tenant.

    Args:
        json_path (Path): Path to the extracted data JSON file.
        llm_client (LLMClient): The LLM client for tenant name resolution.
        yaml_data (list[dict[str, Any]] | None): Optional provided YAML config.

    Returns:
        tuple[list[PageData], list[dict[str, Any]] | None]: The updated pages list and the resulting or provided yaml data configuration.
    """
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
    
    # YAML check
    allowed_tenants = None
    yaml_timelines = []
    
    if yaml_data is not None:
        logger.info("Found yaml_data. Skipping strict anchor logic.")
        allowed_tenants = [t["name"] for t in yaml_data]
        for t in yaml_data:
            end_d = t.get("end_date")
            max_d = "9999-12-31" if end_d == "present" else end_d
            yaml_timelines.append(TenantTimeline(
                canonical_name=t["name"],
                min_date=t["start_date"],
                max_date=max_d
            ))
    else:
        logger.info("Didn't find yaml_data, using the anchor method.")
    
    llm_map = canonicalize_with_llm(representatives, llm_client, allowed_tenants=allowed_tenants)
    for rep, canon in llm_map.items():
        logger.info(f"LLM normalized representative: '{rep}' -> '{canon}'")
    
    final_mapping = {}
    for raw, rep in fuzzy_map.items():
        final_mapping[raw] = llm_map.get(rep, rep)
        
    logger.info("\n>>> TIMELINE BUILDING")
    if yaml_timelines:
        timelines = yaml_timelines
        # yaml_data is already set from the parameter
    else:
        timelines = build_tenant_timelines(pages, final_mapping, allowed_tenants=allowed_tenants)
        # Build yaml_data in memory from computed timelines
        yaml_data = []
        for t in timelines:
            # Check if this is the latest timeline
            is_latest = (t == sorted(timelines, key=lambda x: x.max_date)[-1]) if timelines else False
            end_d = "present" if is_latest else t.max_date
            yaml_data.append({
                "name": t.canonical_name,
                "start_date": t.min_date,
                "end_date": end_d
            })
        if yaml_data:
            logger.info(f"Auto-generated tenant config with {len(yaml_data)} tenant(s)")
    
    logger.info("\n>>> FINAL OUTPUT FOR EACH DOCUMENT")
    assign_pages_to_tenants(pages, timelines, final_mapping)
    
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
    return pages, yaml_data
