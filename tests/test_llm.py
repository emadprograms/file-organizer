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
    b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
)


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


def test_continuation_detection(monkeypatch):
    """Test that pipeline correctly groups continuation pages."""
    # Define 3 classification responses
    responses = [
        PageClassification(house_number="683", resident="محمد", category=Category.CONTRACT, is_continuation=False),
        PageClassification(house_number="683", resident="محمد", category=Category.CONTRACT, is_continuation=True),
        PageClassification(house_number="683", resident="أحمد", category=Category.BASIC_DETAILS, is_continuation=False),
    ]
    call_idx = [0]

    def mock_classify_page(image_bytes, previous_summary=""):
        idx = call_idx[0]
        call_idx[0] += 1
        return responses[idx]

    def mock_extract_pages(self, pdf_path):
        for i in range(3):
            yield (i, DUMMY_IMAGE)

    monkeypatch.setattr(PdfIngestor, "extract_pages_as_images", mock_extract_pages)

    pipeline = Pipeline(api_keys=["test-key"])
    monkeypatch.setattr(pipeline.client, "classify_page", mock_classify_page)

    documents = pipeline.process_pdf("dummy.pdf")

    assert len(documents) == 2
    # First group: pages 0-1 (contract, continuation)
    assert documents[0].start_page == 0
    assert documents[0].end_page == 1
    assert documents[0].category == Category.CONTRACT
    # Second group: page 2 (new topic)
    assert documents[1].start_page == 2
    assert documents[1].end_page == 2
    assert documents[1].category == Category.BASIC_DETAILS


def test_sliding_window(monkeypatch):
    """Test that previous_summary context is passed correctly between groups."""
    summaries_received = []

    responses = [
        PageClassification(house_number="683", resident="محمد", category=Category.CONTRACT, is_continuation=False),
        PageClassification(house_number="683", resident="محمد", category=Category.CONTRACT, is_continuation=True),
        PageClassification(house_number="683", resident="أحمد", category=Category.BASIC_DETAILS, is_continuation=False),
        PageClassification(house_number="683", resident="أحمد", category=Category.BASIC_DETAILS, is_continuation=True),
    ]
    call_idx = [0]

    def mock_classify_page(image_bytes, previous_summary=""):
        summaries_received.append(previous_summary)
        idx = call_idx[0]
        call_idx[0] += 1
        return responses[idx]

    def mock_extract_pages(self, pdf_path):
        for i in range(4):
            yield (i, DUMMY_IMAGE)

    monkeypatch.setattr(PdfIngestor, "extract_pages_as_images", mock_extract_pages)

    pipeline = Pipeline(api_keys=["test-key"])
    monkeypatch.setattr(pipeline.client, "classify_page", mock_classify_page)

    documents = pipeline.process_pdf("dummy.pdf")

    # Page 0: no prior context (first page)
    assert summaries_received[0] == ""
    # Page 1: continuation, still in same group
    assert summaries_received[1] == ""
    # Page 2: new topic — but classify runs before emit, so still ""
    assert summaries_received[2] == ""
    # Page 3: continuation — previous group was emitted when page 2 started new topic,
    # so now previous_summary should contain info from the first group
    assert summaries_received[3] != ""
    assert "contract" in summaries_received[3].lower()

    # Verify document grouping
    assert len(documents) == 2
    assert documents[0].start_page == 0
    assert documents[0].end_page == 1
    assert documents[1].start_page == 2
    assert documents[1].end_page == 3
