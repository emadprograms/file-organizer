import pytest
from pydantic import ValidationError
from src.core.schemas import DocumentGroup, GroupEntry, GroupingResponse

def test_document_group_valid():
    doc = DocumentGroup(
        start_page=0,
        end_page=5,
        primary_tenant="Tenant A",
        category="Reports",
        dates=["2023-01-01"],
        reason="Consistent tenant and category"
    )
    assert doc.start_page == 0
    assert doc.end_page == 5
    assert doc.is_direct_routed is False # default

def test_document_group_invalid_types():
    with pytest.raises(ValidationError):
        # start_page should be int
        DocumentGroup(
            start_page="zero", 
            end_page=5,
            primary_tenant="Tenant A",
            category="Reports",
            dates=["2023-01-01"]
        )

def test_group_entry_valid():
    entry = GroupEntry(
        start_page=0,
        end_page=2,
        reason="Related content",
        brief_arabic_title="عنوان تجريبي"
    )
    assert entry.start_page == 0
    assert entry.brief_arabic_title == "عنوان تجريبي"

def test_grouping_response_valid():
    groups = [
        GroupEntry(start_page=0, end_page=2, reason="R1", brief_arabic_title="T1"),
        GroupEntry(start_page=3, end_page=5, reason="R2", brief_arabic_title="T2")
    ]
    resp = GroupingResponse(groups=groups)
    assert len(resp.groups) == 2
    assert resp.groups[0].start_page == 0

def test_grouping_response_invalid():
    with pytest.raises(ValidationError):
        # groups should be a list of GroupEntry
        GroupingResponse(groups="not a list")
