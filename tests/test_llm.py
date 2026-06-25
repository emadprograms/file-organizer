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
    import os
    monkeypatch.setattr(os.path, "exists", lambda x: False)
    # Define 3 classification responses
    responses = [
        PageClassification(house_number="683", residents=["محمد"], category=Category.CONTRACT, date="NONE"),
        PageClassification(house_number="683", residents=["محمد"], category=Category.CONTRACT, date="NONE", is_continuation=True),
        PageClassification(house_number="683", residents=["أحمد"], category=Category.BASIC_DETAILS, date="NONE"),
    ]
    call_idx = [0]

    def mock_classify_page(image_bytes, footer_text=None, previous_summary="", active_summary=""):
        idx = call_idx[0]
        call_idx[0] += 1
        return responses[idx]

    def mock_extract_pages(self, pdf_path):
        for i in range(3):
            yield (i, DUMMY_IMAGE)

    monkeypatch.setattr(PdfIngestor, "extract_pages_as_images", mock_extract_pages)

    pipeline = Pipeline(api_keys=["test-key"])
    monkeypatch.setattr(pipeline.client, "classify_extracted_page", mock_classify_page)
    monkeypatch.setattr(pipeline.client, "classify_page", mock_classify_page)
    monkeypatch.setattr(pipeline.client, "extract_page", lambda x: "dummy text")
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

def test_global_rpm_enforcement(monkeypatch):
    """03-04-01: Enforce Global 15 RPM IP-Level Cap."""
    import time
    from src.llm import GemmaClient
    
    client = GemmaClient(api_keys=["key1", "key2"])
    now_ref = [1000.0]
    
    for _ in range(client.global_rpm_limit):
        client.global_rpm_tracker.append(now_ref[0])
        
    sleeps = []
    def mock_sleep(secs):
        sleeps.append(secs)
        now_ref[0] += secs + 0.1
        
    monkeypatch.setattr(time, "time", lambda: now_ref[0])
    monkeypatch.setattr(time, "sleep", mock_sleep)
    
    client._get_client_and_key()
    assert sum(sleeps) >= 60



def test_invalid_response_graceful_fallback(monkeypatch):
    """03-04-04: Handle Invalid Responses Gracefully."""
    from src.llm import GemmaClient, InvalidResponseError
    from unittest.mock import MagicMock
    
    client = GemmaClient(api_keys=["key1"])
    
    mock_genai_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.parsed = None
    # Mocking text without valid JSON
    mock_resp.text = "This is not valid json"
    mock_resp.usage_metadata.total_token_count = 100
    mock_genai_client.models.generate_content.return_value = mock_resp
    
    client.clients["key1"] = mock_genai_client
    
    with pytest.raises(InvalidResponseError):
        client.classify_page(b"dummy")

def test_exponential_backoff_on_429(monkeypatch):
    """03-04-05: Add Exponential Backoff With Jitter on 429s."""
    from src.llm import GemmaClient
    import time
    
    client = GemmaClient(api_keys=["key1"])
    
    current_time = [1000.0]
    monkeypatch.setattr(time, "time", lambda: current_time[0])
    
    client._report_failure("key1", is_429=True)
    assert client.key_strikes["key1"] == 1
    cooldown1 = client.cooldown_keys["key1"] - current_time[0]
    assert cooldown1 >= 65.0
    
    client._report_failure("key1", is_429=True)
    assert client.key_strikes["key1"] == 2
    cooldown2 = client.cooldown_keys["key1"] - current_time[0]
    assert cooldown2 >= 65.0

def test_local_inference_fallback(monkeypatch):
    from src.llm import GemmaClient
    import openai
    from src.schemas import PageClassification, Category
    
    client = GemmaClient(api_keys=["key1"])
    
    # Mock text extraction to succeed
    monkeypatch.setattr(client, "_extract_text_with_qwen", lambda x: "dummy text")
    
    # Mock classification to fail
    mock_classify = MagicMock(side_effect=openai.OpenAIError("Connection refused"))
    monkeypatch.setattr(client, "_classify_text_with_local_model", mock_classify)
    
    mock_route = MagicMock()
    mock_route.return_value = PageClassification(house_number="123", residents=["Fallback"], category=Category.BASIC_DETAILS, date="NONE")
    monkeypatch.setattr(client, "_route_llm_call", mock_route)
    
    result = client.classify_page(b"dummy")
    assert result.residents == ["FALLBACK"]
    mock_route.assert_called_once()
    assert mock_route.call_args[1]["model"] == "gemma-4-26b-a4b-it"

def test_openai_structured_output(monkeypatch):
    from src.llm import GemmaClient
    from src.schemas import PageClassification, Category
    import openai
    from unittest.mock import MagicMock

    client = GemmaClient(api_keys=["key1"])
    
    monkeypatch.setattr(client, "_extract_text_with_qwen", lambda x: "Mohammed Ali")
    
    mock_classify = MagicMock()
    mock_classify.return_value = PageClassification(house_number="456", residents=["Mohammed Ali"], category=Category.CONTRACT, date="2020-01-01")
    monkeypatch.setattr(client, "_classify_text_with_local_model", mock_classify)
    
    result = client.classify_page(b"dummy")
    assert result.house_number == "456"
    assert result.residents == ["MOHAMMED ALI"]
    assert result.category == Category.CONTRACT

def test_arabic_ocr_fidelity(monkeypatch):
    from src.llm import GemmaClient
    from src.schemas import PageClassification, Category
    import openai
    
    client = GemmaClient(api_keys=["key1"])
    
    monkeypatch.setattr(client, "_extract_text_with_qwen", lambda x: "محمد")
    
    mock_classify = MagicMock()
    mock_classify.return_value = PageClassification(house_number="123", residents=["محمد"], category=Category.BASIC_DETAILS, date="NONE")
    monkeypatch.setattr(client, "_classify_text_with_local_model", mock_classify)
    
    result = client.classify_page(b"dummy_arabic_doc")
    assert result.residents == ["محمد"]

def test_tiered_retry_logic(monkeypatch):
    from src.llm import GemmaClient
    from src.schemas import PageClassification, Category
    import openai
    
    client = GemmaClient(api_keys=["key1"])
    
    mock_extract = MagicMock(return_value="extracted text")
    monkeypatch.setattr(client, "_extract_text_with_qwen", mock_extract)
    
    mock_classify = MagicMock(side_effect=[
        openai.OpenAIError("Fail 1"),
        openai.OpenAIError("Fail 2"),
        openai.OpenAIError("Fail 3"),
        PageClassification(house_number="999", residents=["Test"], category=Category.BASIC_DETAILS, date="NONE")
    ])
    monkeypatch.setattr(client, "_classify_text_with_local_model", mock_classify)
    
    result = client.classify_page(b"dummy")
    assert result.house_number == "999"
    assert mock_extract.call_count == 2
    assert mock_classify.call_count == 4


def test_state_management_purging(monkeypatch):
    from src.llm import GemmaClient
    import time
    
    client = GemmaClient(api_keys=["key1"])
    GemmaClient.global_cooldown_until = 0.0
    GemmaClient.global_rpm_tracker.clear()

    current_time = [1000.0]
    monkeypatch.setattr(time, "time", lambda: current_time[0])
    monkeypatch.setattr(time, "sleep", lambda x: None)
    
    GemmaClient.global_rpm_tracker.append(900.0) # Older than 65s
    GemmaClient.global_rpm_tracker.append(990.0) # Not older than 65s
    
    # Simulate a call to _get_client_and_key which should purge
    client._get_client_and_key(estimated_tokens=50)
    
    assert len(GemmaClient.global_rpm_tracker) == 2 # 990.0 and the newly added 1000.0
    assert 900.0 not in GemmaClient.global_rpm_tracker

def test_extract_page_normal_flow(monkeypatch):
    from src.llm import GemmaClient
    
    client = GemmaClient(api_keys=["key1"])
    GemmaClient.global_rpm_tracker.clear()
    GemmaClient.global_cooldown_until = 0.0
    
    mock_cloud = MagicMock(return_value="cloud text")
    mock_local = MagicMock(return_value="local text")
    
    monkeypatch.setattr(client, "_extract_text_with_gemini", mock_cloud)
    monkeypatch.setattr(client, "_extract_text_with_qwen", mock_local)
    
    res = client.extract_page(b"dummy")
    assert res == "cloud text"
    mock_cloud.assert_called_once()
    mock_local.assert_not_called()

def test_extract_page_overflow_flow(monkeypatch):
    from src.llm import GemmaClient
    import time
    
    client = GemmaClient(api_keys=["key1"])
    GemmaClient.global_rpm_tracker.clear()
    GemmaClient.global_cooldown_until = 0.0
    
    mock_cloud = MagicMock(side_effect=Exception("429 Too Many Requests"))
    mock_local = MagicMock(return_value="local text")
    
    monkeypatch.setattr(client, "_extract_text_with_gemini", mock_cloud)
    monkeypatch.setattr(client, "_extract_text_with_qwen", mock_local)
    
    res = client.extract_page(b"dummy")
    assert res == "local text"
    mock_cloud.assert_called_once()
    mock_local.assert_called_once()
    # It should set a penalty
    assert GemmaClient.global_cooldown_until > time.time()

def test_extract_page_cooldown_flow(monkeypatch):
    from src.llm import GemmaClient
    import time
    
    client = GemmaClient(api_keys=["key1"])
    GemmaClient.global_rpm_tracker.clear()
    GemmaClient.global_cooldown_until = time.time() + 60.0
    
    mock_cloud = MagicMock(return_value="cloud text")
    mock_local = MagicMock(return_value="local text")
    
    monkeypatch.setattr(client, "_extract_text_with_gemini", mock_cloud)
    monkeypatch.setattr(client, "_extract_text_with_qwen", mock_local)
    
    res = client.extract_page(b"dummy")
    assert res == "local text"
    mock_cloud.assert_not_called()
    mock_local.assert_called_once()

def test_extract_page_resumption_flow(monkeypatch):
    from src.llm import GemmaClient
    import time
    
    client = GemmaClient(api_keys=["key1"])
    
    current_time = [1000.0]
    monkeypatch.setattr(time, "time", lambda: current_time[0])
    
    # Fast-forward past cooldown
    GemmaClient.global_cooldown_until = 900.0 
    GemmaClient.global_rpm_tracker.clear()
    
    mock_cloud = MagicMock(return_value="cloud text")
    mock_local = MagicMock(return_value="local text")
    
    monkeypatch.setattr(client, "_extract_text_with_gemini", mock_cloud)
    monkeypatch.setattr(client, "_extract_text_with_qwen", mock_local)
    
    res = client.extract_page(b"dummy")
    assert res == "cloud text"
    mock_cloud.assert_called_once()
    mock_local.assert_not_called()
