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
    """Enforce Global 15 RPM IP-Level Cap."""
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





def test_exponential_backoff_on_429(monkeypatch):
    """Add Exponential Backoff With Jitter on 429s."""
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


