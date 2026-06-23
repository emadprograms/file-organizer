import pytest
from unittest.mock import MagicMock, patch

from src.schemas import Category, PageClassification
from src.llm import GemmaClient


# Minimal 1x1 pixel PNG for testing (no real image content needed)
MINIMAL_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
    b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
    b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
    b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
)


@pytest.fixture
def mock_api_response():
    return PageClassification(
        house_number="683",
        residents=["محمد"],
        category=Category.BASIC_DETAILS,
        date="NONE"
    )


@pytest.fixture
def mock_continuation_response():
    return PageClassification(
        house_number="683",
        residents=["محمد"],
        category=Category.BASIC_DETAILS,
        date="NONE"
    )


@pytest.fixture
def mock_none_resident_response():
    return PageClassification(
        house_number="683",
        residents=["NONE"],
        category=Category.AMAR_TAKHSEES,
        date="NONE"
    )


@pytest.fixture
def sample_image_bytes():
    return MINIMAL_PNG


@pytest.fixture
def mock_gemma_client(monkeypatch, mock_api_response):
    client = GemmaClient(api_keys=["test-key"])
    monkeypatch.setattr(client, "classify_page", lambda **kwargs: mock_api_response)
    return client
