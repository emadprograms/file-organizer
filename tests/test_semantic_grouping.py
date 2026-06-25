import pytest
import os
from unittest.mock import patch, MagicMock
from src.pipeline import Pipeline
from src.schemas import PageClassification, Category, BulkSemanticMatchResult

def _make_page(house="123", residents=["NONE"], category=Category.OTHER_LETTERS, date="NONE", summary=""):
    return PageClassification(
        house_number=house, residents=residents, category=category, date=date, summary=summary
    )

@patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"})
def test_date_interpolation_standard():
    pipeline = Pipeline(use_local_llm=True)
    raw_pages = [
        (1, _make_page(date="2010-01-01")),
        (2, _make_page(date="NONE")),
        (3, _make_page(date="1000-01-01")), # Outlier
        (4, _make_page(date="2010-01-05")),
    ]
    pipeline._interpolate_dates(raw_pages)
    assert raw_pages[0][1].date == "2010-01-01"
    assert raw_pages[1][1].date == "2010-01-01"
    assert raw_pages[2][1].date == "2010-01-01" 
    assert raw_pages[3][1].date == "2010-01-05"

@patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"})
def test_date_interpolation_all_none_or_outlier():
    pipeline = Pipeline(use_local_llm=True)
    raw_pages = [
        (1, _make_page(date="NONE")),
        (2, _make_page(date="2080-01-01")), # Future Outlier
        (3, _make_page(date="NONE")),
    ]
    pipeline._interpolate_dates(raw_pages)
    assert raw_pages[0][1].date == "NONE"
    assert raw_pages[1][1].date == "NONE"
    assert raw_pages[2][1].date == "NONE"

@patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"})
def test_date_interpolation_backward_fill():
    pipeline = Pipeline(use_local_llm=True)
    raw_pages = [
        (1, _make_page(date="NONE")),
        (2, _make_page(date="NONE")),
        (3, _make_page(date="2012-05-10")),
    ]
    pipeline._interpolate_dates(raw_pages)
    assert raw_pages[0][1].date == "2012-05-10"
    assert raw_pages[1][1].date == "2012-05-10"
    assert raw_pages[2][1].date == "2012-05-10"

@patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"})
def test_alias_mapping_standard():
    pipeline = Pipeline(use_local_llm=True)
    raw_pages = [
        (1, _make_page(residents=["MOHAMED ALI"], category=Category.CONTRACT)),
        (2, _make_page(residents=["FATIMA (WIFE)"], category=Category.PERSONAL_DETAILS)),
        (3, _make_page(residents=["MOHAMED ALI"], category=Category.OTHER_LETTERS)),
    ]
    canonical_mapping = pipeline._map_aliases(raw_pages)
    assert canonical_mapping.get("FATIMA (WIFE)") == "MOHAMED ALI"

@patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"})
def test_alias_mapping_frequency_based():
    pipeline = Pipeline(use_local_llm=True)
    # No anchor docs, but SAAD appears 4 times
    raw_pages = [
        (1, _make_page(residents=["SAAD"], category=Category.OTHER_LETTERS)),
        (2, _make_page(residents=["SAAD"], category=Category.OTHER_LETTERS)),
        (3, _make_page(residents=["SAAD"], category=Category.OTHER_LETTERS)),
        (4, _make_page(residents=["SAAD"], category=Category.OTHER_LETTERS)),
        (5, _make_page(residents=["OMAR (SON)"], category=Category.PERSONAL_DETAILS)),
    ]
    canonical_mapping = pipeline._map_aliases(raw_pages)
    assert canonical_mapping.get("OMAR (SON)") == "SAAD"

@patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"})
def test_alias_mapping_no_primary_tenant():
    pipeline = Pipeline(use_local_llm=True)
    raw_pages = [
        (1, _make_page(residents=["SOMEONE"], category=Category.OTHER_LETTERS)),
        (2, _make_page(residents=["OMAR (SON)"], category=Category.PERSONAL_DETAILS)),
    ]
    canonical_mapping = pipeline._map_aliases(raw_pages)
    # Shouldn't map to anything because "SOMEONE" isn't an anchor nor >3 frequency
    assert "OMAR (SON)" not in canonical_mapping

@patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"})
def test_bulk_semantic_grouping_standard():
    pipeline = Pipeline(use_local_llm=True)
    raw_pages = [
        (1, _make_page(residents=["MOHAMED ALI"], category=Category.CONTRACT)),
        (2, _make_page(residents=["MOHAMED ALI"], category=Category.CONTRACT)),
        (3, _make_page(residents=["MOHAMED ALI"], category=Category.OTHER_LETTERS)),
    ]
    
    pipeline.client.check_bulk_semantic_grouping = MagicMock(return_value=BulkSemanticMatchResult(groups=[[1, 2], [3]]))
    
    docs = pipeline._group_pages_into_documents(raw_pages, {})
    assert len(docs) == 2
    assert docs[0].start_page == 1
    assert docs[0].end_page == 2
    assert docs[0].category == Category.CONTRACT
    assert docs[1].start_page == 3
    assert docs[1].end_page == 3
    assert docs[1].category == Category.OTHER_LETTERS

@patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"})
def test_bulk_semantic_grouping_chunking():
    pipeline = Pipeline(use_local_llm=True)
    # Generate 55 pages to test > 50 chunking
    raw_pages = [(i, _make_page(category=Category.OTHER_LETTERS)) for i in range(1, 56)]
    
    # Mock return values for two chunks
    pipeline.client.check_bulk_semantic_grouping = MagicMock(side_effect=[
        BulkSemanticMatchResult(groups=[list(range(1, 51))]), # First chunk returns 1 group of 50
        BulkSemanticMatchResult(groups=[list(range(51, 56))]) # Second chunk returns 1 group of 5
    ])
    
    docs = pipeline._group_pages_into_documents(raw_pages, {})
    assert pipeline.client.check_bulk_semantic_grouping.call_count == 2
    assert len(docs) == 2
    assert docs[0].start_page == 1
    assert docs[0].end_page == 50
    assert docs[1].start_page == 51
    assert docs[1].end_page == 55

@patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"})
def test_bulk_semantic_grouping_tenant_resolution():
    pipeline = Pipeline(use_local_llm=True)
    raw_pages = [
        (1, _make_page(residents=["ALI"], category=Category.CONTRACT)),
        (2, _make_page(residents=["FATIMA"], category=Category.CONTRACT)),
        (3, _make_page(residents=["UNKNOWN", "ALI"], category=Category.CONTRACT)),
    ]
    canonical_mapping = {"FATIMA": "ALI"}
    pipeline.client.check_bulk_semantic_grouping = MagicMock(return_value=BulkSemanticMatchResult(groups=[[1, 2, 3]]))
    
    docs = pipeline._group_pages_into_documents(raw_pages, canonical_mapping)
    assert len(docs) == 1
    # ALI appears directly twice, and FATIMA maps to ALI. Total ALI = 3.
    assert docs[0].primary_tenant == "ALI"

@patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"})
def test_bulk_semantic_grouping_empty():
    pipeline = Pipeline(use_local_llm=True)
    docs = pipeline._group_pages_into_documents([], {})
    assert len(docs) == 0
