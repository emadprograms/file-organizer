import pytest
from src.core.models import PageData, TenantTimeline
from src.timeline.phase import assign_pages_to_tenants

def test_assign_pages_with_arabic_numeral_dates():
    """
    Test that pages are assigned to the correct tenant even if timelines
    have dates with Arabic numerals. Before the fix, '٢٠١٣' > '2024'.
    """
    # Setup timelines with Arabic numerals
    t1 = TenantTimeline(canonical_name="Tenant 1", min_date="٢٠١٣-٠١-٠١", max_date="٢٠٢٣-١٢-٣١")
    t2 = TenantTimeline(canonical_name="Tenant 2", min_date="٢٠٢٤-٠١-٠١", max_date="9999-12-31")
    timelines = [t1, t2]
    
    # Page with a resolved_date inside t1's range (using ASCII digits)
    p1 = PageData(
        category="test",
        content_explanation="test",
        original_index=0,
        resolved_date="2020-05-15"
    )
    
    # Page inside t2's range (using ASCII digits)
    p2 = PageData(
        category="test",
        content_explanation="test",
        original_index=1,
        resolved_date="2024-05-15"
    )
    
    # Page with Arabic numerals in resolved_date
    p3 = PageData(
        category="test",
        content_explanation="test",
        original_index=2,
        resolved_date="٢٠١٥-٠٥-١٥"
    )

    pages = [p1, p2, p3]
    
    assign_pages_to_tenants(pages, timelines, {})
    
    assert p1.canonical_tenant == "Tenant 1"
    assert p2.canonical_tenant == "Tenant 2"
    assert p3.canonical_tenant == "Tenant 1"

def test_latest_tenant_fallback_with_arabic_numerals():
    """
    Test that a page without a resolved date correctly falls back to the latest
    tenant, even when comparing Arabic numerals with ASCII ones.
    """
    t1 = TenantTimeline(canonical_name="Tenant 1", min_date="٢٠١٣-٠١-٠١", max_date="٢٠١٨-١٢-٣١")
    # t3 max date is 2025, t1 max date is 2018 (in Arabic). 
    # Without normalization, "٢٠١٨" > "2025".
    t2 = TenantTimeline(canonical_name="Tenant ASCII", min_date="2024-01-01", max_date="2025-12-31")
    
    timelines = [t1, t2]
    
    p_no_date = PageData(
        category="test",
        content_explanation="test",
        original_index=0,
        resolved_date=None
    )
    
    assign_pages_to_tenants([p_no_date], timelines, {})
    
    # The latest max_date is 2025-12-31, so Tenant ASCII should be the fallback
    assert p_no_date.canonical_tenant == "Tenant ASCII"
