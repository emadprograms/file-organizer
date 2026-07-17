import pytest
from src.core.models import PageData, TenantTimeline
from src.timeline.timeline_builder import build_tenant_timelines
from src.timeline.phase import assign_pages_to_tenants

def test_anchor_logic_bypass():
    # Only 1 page, 0 anchors -> Normally rejected
    pages = [
        PageData(
            original_index=0,
            text="hello",
            content_explanation="test",
            category="other",
            expected_tenant_name="Tenant A",
            resolved_date="2023-01-01"
        )
    ]
    mapping = {"Tenant A": "Tenant A"}
    
    # Without allowed_tenants, should return empty
    timelines_strict = build_tenant_timelines(pages, mapping)
    assert len(timelines_strict) == 0
    
    # With allowed_tenants, should bypass threshold and return the timeline
    timelines_bypassed = build_tenant_timelines(pages, mapping, allowed_tenants=["Tenant A"])
    assert len(timelines_bypassed) == 1
    assert timelines_bypassed[0].canonical_name == "Tenant A"

def test_timeline_fallback_overlap():
    pages = [
        PageData(
            original_index=0,
            text="hello",
            content_explanation="test",
            category="other",
            expected_tenant_name=None,
            resolved_date="2023-06-01"
        )
    ]
    
    timelines = [
        TenantTimeline(canonical_name="Tenant A", min_date="2023-01-01", max_date="2023-12-31"),
        TenantTimeline(canonical_name="Tenant B", min_date="2023-05-01", max_date="2024-12-31")
    ]
    
    # Overlap on 2023-06-01. Tenant B started later (2023-05-01 > 2023-01-01), so Tenant B is the latest.
    assign_pages_to_tenants(pages, timelines, {})
    assert pages[0].canonical_tenant == "Tenant B"

def test_timeline_fallback_no_date():
    pages = [
        PageData(
            original_index=0,
            text="hello",
            content_explanation="test",
            category="other",
            expected_tenant_name=None,
            resolved_date=None
        )
    ]
    
    timelines = [
        TenantTimeline(canonical_name="Tenant A", min_date="2022-01-01", max_date="2022-12-31"),
        TenantTimeline(canonical_name="Tenant B", min_date="2023-01-01", max_date="9999-12-31") # "present"
    ]
    
    assign_pages_to_tenants(pages, timelines, {})
    assert pages[0].canonical_tenant == "Tenant B"
