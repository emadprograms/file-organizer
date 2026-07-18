import logging
from src.core.models import PageData, TenantTimeline

logger = logging.getLogger(f"file_organizer.{__name__}")

def build_tenant_timelines(
    pages: list[PageData], 
    canonical_mapping: dict[str, str], 
    allowed_tenants: list[str] | None = None
) -> list[TenantTimeline]:
    """Build chronological timelines for each tenant based on extracted page data.

    Qualifies tenants based on minimum page counts and anchor documents. If 
    allowed_tenants is provided, standard qualification rules are bypassed.

    Args:
        pages (list[PageData]): The parsed pages with dates and tenant names.
        canonical_mapping (dict[str, str]): Mapping from raw names to canonical names.
        allowed_tenants (list[str] | None): Optional explicit list of allowed tenants.

    Returns:
        list[TenantTimeline]: The generated timelines for qualified tenants.

    Raises:
        RuntimeError: If a timeline has a minimum date later than its maximum date.
    """
    anchor_categories = {"contract", "forms", "id_cards"}
    
    tenant_stats = {}
    for page in pages:
        raw_name = page.expected_tenant_name
        if not raw_name:
            continue
            
        canonical_name = canonical_mapping.get(raw_name, raw_name)
        if canonical_name not in tenant_stats:
            tenant_stats[canonical_name] = {"anchor_count": 0, "total_count": 0, "dates": []}
            
        stats = tenant_stats[canonical_name]
        stats["total_count"] += 1
        
        if page.category in anchor_categories:
            stats["anchor_count"] += 1
            
        if page.resolved_date:
            stats["dates"].append(page.resolved_date)
            
    timelines = []
    for name, stats in tenant_stats.items():
        if allowed_tenants is not None:
            # Skip anchor/page threshold logic if allowed_tenants is provided
            if name in allowed_tenants:
                if stats["dates"]:
                    min_date = min(stats["dates"])
                    max_date = max(stats["dates"])
                    if min_date > max_date:
                        raise RuntimeError(f"min_date {min_date} > max_date {max_date}")
                    logger.info(f"Accepted Tenant '{name}' via allowed_tenants override -> Timeline: {min_date} to {max_date}")
                    timelines.append(TenantTimeline(
                        canonical_name=name,
                        min_date=min_date,
                        max_date=max_date
                    ))
                else:
                    logger.info(f"Accepted Tenant '{name}' via allowed_tenants override, but missing valid dates.")
            else:
                logger.info(f"Rejected Tenant '{name}': Not in allowed_tenants list.")
        else:
            if stats["anchor_count"] >= 1 and stats["total_count"] >= 5:
                if stats["dates"]:
                    min_date = min(stats["dates"])
                    max_date = max(stats["dates"])
                    if min_date > max_date:
                        raise RuntimeError(f"min_date {min_date} > max_date {max_date}")
                    logger.info(f"Qualified Tenant '{name}': {stats['total_count']} pages, {stats['anchor_count']} anchors -> Timeline: {min_date} to {max_date}")
                    timelines.append(TenantTimeline(
                        canonical_name=name,
                        min_date=min_date,
                        max_date=max_date
                    ))
                else:
                    logger.info(f"Rejected Tenant '{name}': Missing valid dates.")
            else:
                logger.info(f"Rejected Tenant '{name}': {stats['total_count']} pages, {stats['anchor_count']} anchors (Failed threshold of >=1 anchors, >=5 pages)")
                
    return timelines
