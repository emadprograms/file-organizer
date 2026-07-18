from typing import Any
import pytest
from pathlib import Path
import yaml
import logging
from src.tenant_config.yaml_loader import load_tenant_config
from src.core.exceptions import ConfigurationError

def test_load_tenant_config_success(tmp_path: Path) -> None:
    """
    Test load tenant config success.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_dir = tmp_path / "pdfs" / "123"
    source_files_dir = target_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = source_files_dir / "123_tenants.yaml"
    
    config_data = [
        {"name": "Tenant A", "start_date": "2023-01-01", "end_date": "2023-12-31"},
        {"name": "Tenant B", "start_date": "2024-01-01", "end_date": "present"}
    ]
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
        
    tenants = load_tenant_config(target_dir, "123")
    assert tenants == config_data

def test_load_tenant_config_missing_file(tmp_path: Path, caplog) -> None:
    """
    Test load tenant config missing file.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_dir = tmp_path / "pdfs" / "123"
    source_files_dir = target_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    
    # Do not create 123_tenants.yaml
    with caplog.at_level(logging.INFO):
        tenants = load_tenant_config(target_dir, "123")
    
    assert tenants is None
    assert "No 123_tenants.yaml found" in caplog.text

def test_load_tenant_config_malformed_yaml(tmp_path: Path) -> None:
    """
    Test load tenant config malformed yaml.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_dir = tmp_path / "pdfs" / "123"
    source_files_dir = target_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = source_files_dir / "123_tenants.yaml"
    
    # Write invalid yaml
    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write("[unclosed list\n")
        
    with pytest.raises(ConfigurationError, match="Malformed YAML"):
        load_tenant_config(target_dir, "123")

def test_load_tenant_config_missing_keys(tmp_path: Path) -> None:
    """
    Test load tenant config missing keys.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_dir = tmp_path / "pdfs" / "123"
    source_files_dir = target_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = source_files_dir / "123_tenants.yaml"
    
    config_data = [{"name": "Tenant A", "start_date": "2023-01-01"}] # missing end_date
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
        
    with pytest.raises(ConfigurationError, match="Missing 'end_date' in item at index 0"):
        load_tenant_config(target_dir, "123")

def test_load_tenant_config_not_a_list(tmp_path: Path) -> None:
    """
    Test load tenant config not a list.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_dir = tmp_path / "pdfs" / "123"
    source_files_dir = target_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = source_files_dir / "123_tenants.yaml"
    
    config_data = {"tenants": "Not a list"}
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
        
    with pytest.raises(ConfigurationError, match="YAML must be a list of dictionaries"):
        load_tenant_config(target_dir, "123")
