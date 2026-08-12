import pytest
from src.core.models import PageData
import yaml
from pathlib import Path

def test_pagedata_is_continuation_default():
    # Test that default is False
    page = PageData(original_index=0)
    assert page.is_continuation is False

def test_pagedata_is_continuation_set():
    page = PageData(original_index=0, is_continuation=True)
    assert page.is_continuation is True

def test_categories_yaml_contains_continuation_instruction():
    # Verify that the instruction is in the yaml file
    yaml_path = Path("src/core/categories.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        categories = yaml.safe_load(f)
    
    letters_extract = categories.get("letters", {}).get("extract", [])
    continuation_instruction_found = False
    for instruction in letters_extract:
        if "is_continuation" in instruction:
            continuation_instruction_found = True
            break
            
    assert continuation_instruction_found, "The is_continuation instruction is missing from letters in categories.yaml"

