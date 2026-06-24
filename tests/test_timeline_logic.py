import pytest
import os
from unittest.mock import patch
from src.pipeline import Pipeline
from src.schemas import PageClassification, Category

@pytest.fixture
def pipeline():
    with patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"}):
        return Pipeline()

def test_logic_01_large_family(pipeline):
    # Anchor document with 8 resident names
    raw_pages = [
        (1, PageClassification(
            category=Category.BASIC_DETAILS,
            residents=[f"Name {i}" for i in range(8)],
            house_number="123",
            date="2023-01-01",
            is_continuation=False
        ))
    ]
    canonical_mapping = {}
    docs = pipeline._group_pages_into_documents(raw_pages, canonical_mapping)
    assert len(docs) == 1
    assert docs[0].primary_tenant == "NAME 0"  # It takes the first name if no current matches

def test_logic_02_array_order(pipeline):
    # Anchor document where 2nd name matches current_primary_tenant
    raw_pages = [
        (1, PageClassification(
            category=Category.BASIC_DETAILS,
            residents=["CURRENT TENANT NAME"],
            house_number="123",
            date="2023-01-01",
            is_continuation=False
        )),
        (2, PageClassification(
            category=Category.KEY_HANDOVER,
            residents=["NEW SPOUSE", "CURRENT TENANT NAME"],
            house_number="123",
            date="2023-01-02",
            is_continuation=False
        ))
    ]
    canonical_mapping = {}
    docs = pipeline._group_pages_into_documents(raw_pages, canonical_mapping)
    assert len(docs) == 2
    assert docs[0].primary_tenant == "CURRENT TENANT NAME"
    assert docs[1].primary_tenant == "CURRENT TENANT NAME"

def test_logic_03_single_word_names(pipeline):
    raw_pages = [
        (1, PageClassification(
            category=Category.BASIC_DETAILS,
            residents=["MOHAMMED"],
            house_number="123",
            date="2023-01-01",
            is_continuation=False
        )),
        (2, PageClassification(
            category=Category.KEY_HANDOVER,
            residents=["MOHAMMED"],
            house_number="123",
            date="2023-01-02",
            is_continuation=False
        ))
    ]
    canonical_mapping = {}
    docs = pipeline._group_pages_into_documents(raw_pages, canonical_mapping)
    assert len(docs) == 2
    assert docs[0].primary_tenant == "MOHAMMED"
    assert docs[1].primary_tenant == "MOHAMMED"

def test_logic_04_date_grouping(pipeline):
    # Subtest A: is_continuation=False -> 2 groups
    raw_pages_a = [
        (1, PageClassification(category=Category.NOTIFICATIONS, residents=["NONE"], house_number="123", date="2023-01-01", is_continuation=False)),
        (2, PageClassification(category=Category.NOTIFICATIONS, residents=["NONE"], house_number="123", date="2023-01-02", is_continuation=False))
    ]
    docs_a = pipeline._group_pages_into_documents(raw_pages_a, {})
    assert len(docs_a) == 2

    # Subtest B: is_continuation=True -> 1 group
    raw_pages_b = [
        (1, PageClassification(category=Category.NOTIFICATIONS, residents=["NONE"], house_number="123", date="2023-01-01", is_continuation=False)),
        (2, PageClassification(category=Category.NOTIFICATIONS, residents=["NONE"], house_number="123", date="2023-01-02", is_continuation=True))
    ]
    docs_b = pipeline._group_pages_into_documents(raw_pages_b, {})
    assert len(docs_b) == 1
    assert docs_b[0].dates == ["2023-01-01", "2023-01-02"]

def test_logic_05_prefix_rescue(pipeline):
    raw_pages = [
        (1, PageClassification(category=Category.PERSONAL_DETAILS, residents=["NONE"], house_number="123", date="2023-01-01", is_continuation=False)),
        (2, PageClassification(category=Category.BASIC_DETAILS, residents=["ANCHOR NAME"], house_number="123", date="2023-01-02", is_continuation=False))
    ]
    docs = pipeline._group_pages_into_documents(raw_pages, {})
    assert len(docs) == 2
    assert docs[0].primary_tenant == "ANCHOR NAME"
    assert docs[1].primary_tenant == "ANCHOR NAME"

    raw_pages_no_anchor = [
        (1, PageClassification(category=Category.PERSONAL_DETAILS, residents=["NONE"], house_number="123", date="2023-01-01", is_continuation=False))
    ]
    docs_no_anchor = pipeline._group_pages_into_documents(raw_pages_no_anchor, {})
    assert len(docs_no_anchor) == 1
    assert docs_no_anchor[0].primary_tenant == "UNKNOWN"

def test_logic_06_non_anchor_routing(pipeline):
    # Ahmad and Khalid are verified residents via Anchor docs.
    raw_pages = [
        (1, PageClassification(category=Category.BASIC_DETAILS, residents=["AHMAD"], house_number="123", date="2023-01-01", is_continuation=False)),
        (2, PageClassification(category=Category.BASIC_DETAILS, residents=["KHALID"], house_number="123", date="2023-01-02", is_continuation=False)),
        # Notification for Khalid -> should route to Khalid
        (3, PageClassification(category=Category.NOTIFICATIONS, residents=["KHALID"], house_number="123", date="2023-01-03", is_continuation=False)),
        # Notification for RandomName -> ignores and defaults to current_primary_tenant (KHALID)
        (4, PageClassification(category=Category.NOTIFICATIONS, residents=["RANDOM NAME"], house_number="123", date="2023-01-04", is_continuation=False))
    ]
    docs = pipeline._group_pages_into_documents(raw_pages, {})
    assert len(docs) == 4
    assert docs[0].primary_tenant == "AHMAD"
    assert docs[1].primary_tenant == "KHALID"
    assert docs[2].primary_tenant == "KHALID"
    assert docs[3].primary_tenant == "KHALID"
