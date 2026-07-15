import pytest
from pathlib import Path
import yaml
from src.tenant_config.yaml_loader import load_tenant_config
from src.core.exceptions import ConfigurationError

def test_load_tenant_config_success(tmp_path: Path):
    target_dir = tmp_path / "pdfs" / "123"
    target_dir.mkdir(parents=True)
    yaml_file = target_dir / "tenants.yaml"
    
    config_data = {
        "tenants": ["Tenant A", "Tenant B", "Tenant C"]
    }
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
        
    tenants = load_tenant_config(target_dir)
    assert tenants == ["Tenant A", "Tenant B", "Tenant C"]

def test_load_tenant_config_missing_file(tmp_path: Path, caplog):
    target_dir = tmp_path / "pdfs" / "123"
    target_dir.mkdir(parents=True)
    
    # Do not create tenants.yaml
    tenants = load_tenant_config(target_dir)
    
    assert tenants == []
    assert "No tenants.yaml found" in caplog.text

def test_load_tenant_config_malformed_yaml(tmp_path: Path):
    target_dir = tmp_path / "pdfs" / "123"
    target_dir.mkdir(parents=True)
    yaml_file = target_dir / "tenants.yaml"
    
    # Write invalid yaml
    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write("tenants: [unclosed list\n")
        
    with pytest.raises(ConfigurationError, match="Malformed YAML"):
        load_tenant_config(target_dir)

def test_load_tenant_config_missing_tenants_key(tmp_path: Path):
    target_dir = tmp_path / "pdfs" / "123"
    target_dir.mkdir(parents=True)
    yaml_file = target_dir / "tenants.yaml"
    
    config_data = {"other_key": "value"}
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
        
    with pytest.raises(ConfigurationError, match="Missing 'tenants' key"):
        load_tenant_config(target_dir)

def test_load_tenant_config_tenants_not_a_list(tmp_path: Path):
    target_dir = tmp_path / "pdfs" / "123"
    target_dir.mkdir(parents=True)
    yaml_file = target_dir / "tenants.yaml"
    
    config_data = {"tenants": "Not a list"}
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
        
    with pytest.raises(ConfigurationError, match="'tenants' must be a list"):
        load_tenant_config(target_dir)
