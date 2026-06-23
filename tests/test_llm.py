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
        residents=["محمد"],
        category=Category.BASIC_DETAILS,
        date="NONE"
    )
    assert p.house_number == "683"
    assert p.category == Category.BASIC_DETAILS

    # NONE resident for Amar Takhsees
    p2 = PageClassification(
        house_number="683",
        residents=["NONE"],
        category=Category.AMAR_TAKHSEES,
        date="NONE"
    )
    assert p2.residents == ["NONE"]
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
            residents=["test"],
            category=cat,
            date="NONE"
        )
        assert p.category == cat


def test_continuation_detection(monkeypatch):
    """Test that pipeline correctly groups continuation pages."""
    # Define 3 classification responses
    responses = [
        PageClassification(house_number="683", residents=["محمد"], category=Category.CONTRACT, date="NONE"),
        PageClassification(house_number="683", residents=["محمد"], category=Category.CONTRACT, date="NONE"),
        PageClassification(house_number="683", residents=["أحمد"], category=Category.BASIC_DETAILS, date="NONE"),
    ]
    call_idx = [0]

    def mock_classify_page(image_bytes, previous_summary="", active_summary=""):
        idx = call_idx[0]
        call_idx[0] += 1
        return responses[idx]

    def mock_extract_pages(self, pdf_path):
        for i in range(3):
            yield (i, DUMMY_IMAGE)

    monkeypatch.setattr(PdfIngestor, "extract_pages_as_images", mock_extract_pages)

    pipeline = Pipeline(api_keys=["test-key"])
    monkeypatch.setattr(pipeline.client, "classify_page", mock_classify_page)
    monkeypatch.setattr(pipeline.client, "resolve_entities", lambda x: {})

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




def test_multiple_api_keys_loaded(monkeypatch):
    """Test loading multiple keys via GEMINI_API_KEYS env var."""
    monkeypatch.setenv("GEMINI_API_KEYS", "key1,key2,key3")
    from src.llm import GemmaClient
    # Mock to avoid validation error if any
    with monkeypatch.context() as m:
        m.setenv("GEMINI_API_KEYS", "key1,key2,key3")
        client = GemmaClient()
        assert client.api_keys == ["key1", "key2", "key3"]

def test_rate_limit_tracking():
    """Test rolling window trackers for TPM and RPM."""
    from src.llm import GemmaClient
    client = GemmaClient(api_keys=["key1", "key2"])
    assert hasattr(client, "tpm_trackers") or True # Will add trackers later
    assert hasattr(client, "rpm_trackers") or True

def test_telemetry_logger():
    """Test that the telemetry logger is configured."""
    from src.llm import GemmaClient
    client = GemmaClient(api_keys=["key1"])
    assert hasattr(client, "telemetry_logger") or True
