import pytest
import yaml
from pathlib import Path
from src.config import load_user_config, InvalidConfigError

def test_load_valid_config(tmp_path):
    config_content = """
    categories:
      - name: Basic Details
        id: basic_details_form
    extraction:
      strategy: llm
      prompt_template: "Extract {fields}"
      fields:
        - name: residents
          type: list[str]
          description: "Names"
    cleaning:
      strategy: none
    grouping:
      strategy: declarative
      fields: ["residents", "category"]
    routing:
      strategy: template
      destination_format: "{category}/{residents}"
      fallback_folder: "UNKNOWN"
    """
    config_file = tmp_path / "valid.yaml"
    config_file.write_text(config_content)
    
    config = load_user_config(config_file)
    assert len(config.categories) == 1
    assert config.categories[0].name == "Basic Details"

def test_load_invalid_config(tmp_path):
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("invalid: [yaml: broken")
    with pytest.raises(InvalidConfigError):
        load_user_config(config_file)

def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_user_config(Path("non_existent_file.yaml"))
