import pytest

from pydantic import ValidationError


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
