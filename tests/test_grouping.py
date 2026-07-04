import pytest
from src.processing.grouping import category_presplit, verify_groups, merge_chunks
from src.core.schemas import GroupEntry, DocumentGroup
from types import SimpleNamespace

def test_category_presplit():
    pages = [
        SimpleNamespace(category="forms", page_idx=0),
        SimpleNamespace(category="forms", page_idx=1),
        SimpleNamespace(category="letters", page_idx=2),
        SimpleNamespace(category="letters", page_idx=3),
        SimpleNamespace(category="forms", page_idx=4),
    ]
    
    runs = category_presplit(pages)
    assert len(runs) == 3
    assert len(runs[0]) == 2
    assert runs[0][0].category == "forms"
    assert runs[1][0].category == "letters"
    assert runs[2][0].category == "forms"

def test_verification_logic():
    # Valid
    groups = [
        GroupEntry(start_page=0, end_page=2, reason="A", brief_arabic_title="A"),
        GroupEntry(start_page=3, end_page=9, reason="B", brief_arabic_title="B")
    ]
    assert verify_groups(groups, 0, 10) == True
    
    # Gap
    with pytest.raises(ValueError, match="Gap or overlap detected"):
        groups_gap = [
            GroupEntry(start_page=0, end_page=2, reason="A", brief_arabic_title="A"),
            GroupEntry(start_page=4, end_page=9, reason="B", brief_arabic_title="B")
        ]
        verify_groups(groups_gap, 0, 10)
        
    # Overlap
    with pytest.raises(ValueError, match="Gap or overlap detected"):
        groups_overlap = [
            GroupEntry(start_page=0, end_page=3, reason="A", brief_arabic_title="A"),
            GroupEntry(start_page=3, end_page=9, reason="B", brief_arabic_title="B")
        ]
        verify_groups(groups_overlap, 0, 10)
        
    # Bad start
    with pytest.raises(ValueError, match="does not match chunk_start_idx"):
        verify_groups(groups, 1, 10)
        
    # Bad end
    with pytest.raises(ValueError, match="does not match chunk end boundary"):
        verify_groups(groups, 0, 11)

def test_overlap_merge():
    # overlap_page_idx = 9
    # Chunk 1: pages 0-9
    chunk1_groups = [
        DocumentGroup(start_page=0, end_page=5, primary_tenant="T1", category="forms", dates=[]),
        DocumentGroup(start_page=6, end_page=9, primary_tenant="T1", category="forms", dates=[], reason="reason1", brief_arabic_title="title1")
    ]
    
    # Chunk 2: pages 9-15
    chunk2_groups = [
        DocumentGroup(start_page=9, end_page=12, primary_tenant="T2", category="forms", dates=[], reason="reason2", brief_arabic_title="title2"),
        DocumentGroup(start_page=13, end_page=15, primary_tenant="T2", category="forms", dates=[])
    ]
    
    merged = merge_chunks(chunk1_groups, chunk2_groups, 9)
    assert len(merged) == 3
    assert merged[0].end_page == 5
    assert merged[1].start_page == 6
    assert merged[1].end_page == 12
    assert merged[1].reason == "reason1"  # Trust chunk 1
    assert merged[1].brief_arabic_title == "title1" # Trust chunk 1
    assert merged[2].start_page == 13
    assert merged[2].end_page == 15
