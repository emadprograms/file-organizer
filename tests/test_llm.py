import pytest
from unittest.mock import MagicMock, patch
from src.schemas import Category, PageClassification, DocumentGroup
from src.llm import GemmaClient
from src.pipeline import Pipeline
from src.ingest import PdfIngestor

# Minimal 1x1 pixel PNG for test mocking
DUMMY_IMAGE = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
    b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
    b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
    b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82' + b'\x00' * 15000
)





def test_schema_definition():
    """Verify Category has 13 members and PageClassification validates correctly."""
    assert len(Category) == 13

    p = PageClassification(
        house_number="683",
        residents=["محمد"],
        category=Category.BASIC_DETAILS,
        date="NONE"
    , summary="test")
    assert p.house_number == "683"
    assert p.category == Category.BASIC_DETAILS

    # NONE resident for Amar Takhsees
    p2 = PageClassification(
        house_number="683",
        residents=["NONE"],
        category=Category.AMAR_TAKHSEES,
        date="NONE"
    , summary="test")
    assert p2.residents == ["NONE"]
    assert p2.category == Category.AMAR_TAKHSEES





def test_category_classification():
    """Verify all 13 Category enum values are accepted by PageClassification."""
    for cat in Category:
        p = PageClassification(
            house_number="1",
            residents=["test"],
            category=cat,
            date="NONE"
        , summary="test")
        assert p.category == cat








def test_single_api_key_loaded():
    from src.llm import GemmaClient
    client = GemmaClient(api_key="key1")
    assert client.api_key == "key1"
