import pytest
from unittest.mock import MagicMock, patch
from src.pipeline import Pipeline
from src.schemas import PageClassification, Category, UserConfig, ConfigCleaning, ConfigGrouping, ConfigCategory, ConfigExtraction, ConfigRouting

@pytest.fixture
def mock_config_llm_cleaning():
    return UserConfig(
        categories=[ConfigCategory(id="TEST", name="Test")],
        extraction=ConfigExtraction(prompt_template="", fields=[]),
        cleaning=ConfigCleaning(strategy="llm", prompt_template="Clean this"),
        grouping=ConfigGrouping(strategy="declarative"),
        routing=ConfigRouting(strategy="template", destination_format="", fallback_folder="")
    )

def test_run_cleaning_pass_llm(mock_config_llm_cleaning):
    pipeline = Pipeline("dummy")
    raw_pages = [(1, PageClassification(category=Category.BASIC_DETAILS, residents=["Dirty Name"], date="2020-01-01", summary=""))]
    
    with patch("src.llm.LLMClient._route_llm_call") as mock_route:
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

@pytest.fixture
def mock_config_declarative_grouping():
    return UserConfig(
        categories=[ConfigCategory(id="TEST", name="Test")],
        extraction=ConfigExtraction(prompt_template="", fields=[]),
        cleaning=ConfigCleaning(strategy="none"),
        grouping=ConfigGrouping(strategy="declarative", group_by=["category", "residents"]),
        routing=ConfigRouting(strategy="template", destination_format="", fallback_folder="")
    )

def test_group_pages_into_documents(mock_config_declarative_grouping):
    pipeline = Pipeline("dummy")
    raw_pages = [
        (1, PageClassification(category=Category.BASIC_DETAILS, residents=["A"], date="2020-01-01", summary="")),
        (2, PageClassification(category=Category.BASIC_DETAILS, residents=["A"], date="2020-01-02", summary="")),
        (3, PageClassification(category=Category.CONTRACT, residents=["A"], date="2020-01-03", summary=""))
    ]
    
    docs = pipeline._group_pages_into_documents(raw_pages, mock_config_declarative_grouping)
    
    assert len(docs) == 2
    assert docs[0].start_page == 1
    assert docs[0].end_page == 2
    assert docs[1].start_page == 3
    assert docs[1].end_page == 3
