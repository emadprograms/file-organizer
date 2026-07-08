import pytest
import json
import logging

logger = logging.getLogger(f"file_organizer.{__name__}")

@pytest.fixture
def mock_page_data_dict():
    return {
        "category": "contract",
        "content_explanation": "Test explanation",
        "expected_tenant_name": "احمد محمد",
        "date": "2023-05-15",
        "sender": "Ministry",
        "receiver": "Tenant",
        "subject": "Lease Agreement"
    }

@pytest.fixture
def mock_tenant_timeline_dict():
    return {
        "canonical_name": "احمد محمد",
        "min_date": "2023-01-01",
        "max_date": "2023-12-31"
    }
