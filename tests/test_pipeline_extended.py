import pytest

from pydantic import BaseModel
class MockPage(BaseModel):
    category: str
    residents: list[str]
    date: str
    summary: str

from unittest.mock import MagicMock, patch
from src.processing.pipeline import Pipeline
from src.core.schemas import UserConfig, ConfigCleaning, ConfigGrouping, ConfigCategory, ConfigExtraction, ConfigRouting

@pytest.fixture
def mock_config_llm_cleaning():
    return UserConfig(
        categories=[ConfigCategory(id="TEST", name="Test")],
        extraction=ConfigExtraction(prompt_template="", fields=[]),
        cleaning=ConfigCleaning(strategy="llm", prompt_template="Clean this"),
        grouping=ConfigGrouping(strategy="declarative"),
        routing=ConfigRouting(strategy="template", rules={}, fallback_folder="")
    )

def test_run_cleaning_pass_llm(mock_config_llm_cleaning):
    pipeline = Pipeline("dummy")
    raw_pages = [(1, MockPage(category="BASIC_DETAILS", residents=["Dirty Name"], date="2020-01-01", summary=""))]
    
    with patch('src.llm.llm.LLMClient._route_llm_call') as mock_route:
        mock_result = MagicMock()
        mock_page = MagicMock()
        mock_page.page_index = 1
        mock_page.residents = ["Clean Name"]
        mock_page.category = "BASIC_DETAILS"
        mock_page.date = "2020-01-01"
        mock_page.summary = ""
        mock_result.pages = [mock_page]
        mock_route.return_value = mock_result
        
        pipeline._run_cleaning_pass(raw_pages, mock_config_llm_cleaning)
        
        assert raw_pages[0][1].residents == ["Clean Name"]


