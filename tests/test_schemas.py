import pytest
from src.schemas import PageClassification, Category
from pydantic import ValidationError

def test_normalize_category():
    # Test valid exact matching
    pc1 = PageClassification(residents=["Mohamed"], category="Allocation Order", date="2020-01-01", summary="summary")
    assert pc1.category == Category.AMAR_TAKHSEES

    # Test lowercase with underscore (LLM style output)
    pc2 = PageClassification(residents=["Mohamed"], category="allocation_order", date="2020-01-01", summary="summary")
    assert pc2.category == Category.AMAR_TAKHSEES

    # Test lowercase with underscore for another category
    pc3 = PageClassification(residents=["Mohamed"], category="basic_details_form", date="2020-01-01", summary="summary")
    assert pc3.category == Category.BASIC_DETAILS

    # Test exact enum key matching
    pc4 = PageClassification(residents=["Mohamed"], category="AMAR_TAKHSEES", date="2020-01-01", summary="summary")
    assert pc4.category == Category.AMAR_TAKHSEES

    # Test invalid category
    with pytest.raises(ValidationError):
         PageClassification(residents=["Mohamed"], category="Invalid Category", date="2020-01-01", summary="summary")

def test_user_config_loading_with_dynamic_fields():
    import yaml
    from src.schemas import UserConfig
    with open('sample-config.yaml', 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    config = UserConfig(**config_data)
    assert hasattr(config.extraction, "prompt_template")
    assert hasattr(config.extraction, "fields")
    assert len(config.extraction.fields) == 4
    assert config.extraction.fields[0].name == "residents"
    assert config.extraction.fields[0].type == "list[str]"
    assert config.grouping.strategy == "python"
    assert config.grouping.script_path == "./scripts/sample-grouping.py"
    assert config.routing.strategy == "python"
    assert config.routing.fallback_folder == "UNKNOWN"
    assert config.routing.script_path == "./scripts/sample-routing.py"
