import pytest
from src.schemas import Category, PageClassification
from src.llm import GemmaClient


def test_api_connection():
    """Verify GemmaClient can be instantiated with a dummy key."""
    client = GemmaClient(api_keys=["test-key-1234"])
    assert client.api_keys == ["test-key-1234"]
    assert client.current_key_idx == 0
    assert hasattr(client, 'classify_page')


def test_schema_definition():
    """Verify Category has 13 members and PageClassification validates correctly."""
    assert len(Category) == 13

    p = PageClassification(
        house_number="683",
        resident="محمد",
        category=Category.BASIC_DETAILS,
        is_continuation=False
    )
    assert p.house_number == "683"
    assert p.resident == "محمد".upper()  # validator uppercases
    assert p.category == Category.BASIC_DETAILS
    assert p.is_continuation is False

    # NONE resident for Amar Takhsees
    p2 = PageClassification(
        house_number="683",
        resident="NONE",
        category=Category.AMAR_TAKHSEES,
        is_continuation=False
    )
    assert p2.resident == "NONE"
    assert p2.category == Category.AMAR_TAKHSEES


def test_page_classification(mock_gemma_client, sample_image_bytes):
    """Verify mocked classify_page returns valid PageClassification."""
    result = mock_gemma_client.classify_page(image_bytes=sample_image_bytes)
    assert isinstance(result, PageClassification)
    assert result.house_number == "683"


def test_category_classification():
    """Verify all 13 Category enum values are accepted by PageClassification."""
    for cat in Category:
        p = PageClassification(
            house_number="1",
            resident="test",
            category=cat,
            is_continuation=False
        )
        assert p.category == cat


@pytest.mark.skip(reason="Requires sliding window from Plan 03")
def test_continuation_detection():
    pass


@pytest.mark.skip(reason="Requires sliding window from Plan 03")
def test_sliding_window():
    pass
