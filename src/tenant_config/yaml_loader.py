import yaml
from pathlib import Path
import logging
from src.core.exceptions import ConfigurationError

logger = logging.getLogger(f"file_organizer.{__name__}")

from typing import Any

def load_tenant_config(target_dir: Path, house_id: str) -> list[dict[str, Any]] | None:
    """Load tenant names and timelines from a configuration file.
    
    Reads the {house_id}_tenants.yaml file located in the .source_files directory 
    of the target directory.
    
    Args:
        target_dir (Path): The directory containing the .source_files folder where the yaml is expected.
        house_id (str): The house ID to prefix the yaml file name.
        
    Returns:
        list[dict[str, Any]] | None: A list of dictionaries representing tenant configuration, or None if the file is missing.
        
    Raises:
        ConfigurationError: If the YAML file is malformed, invalid, or missing required keys.
    """
    yaml_path = target_dir / ".source_files" / f"{house_id}_1_tenants.yaml"
    if not yaml_path.exists():
        yaml_path = target_dir / ".source_files" / f"{house_id}_tenants.yaml"
    
    if not yaml_path.exists():
        logger.info(f"No {yaml_path.name} found in {target_dir / '.source_files'}. Falling back to anchor logic.")
        return None
        
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or []
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Malformed YAML in {yaml_path}: {e}") from e
        
    if not isinstance(data, list):
        raise ConfigurationError(f"YAML must be a list of dictionaries in {yaml_path}")
        
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ConfigurationError(f"Item at index {idx} in {yaml_path} must be a dictionary.")
        if "name" not in item:
            raise ConfigurationError(f"Missing 'name' in item at index {idx} in {yaml_path}")
        if "start_date" not in item:
            raise ConfigurationError(f"Missing 'start_date' in item at index {idx} in {yaml_path}")
        if "end_date" not in item:
            raise ConfigurationError(f"Missing 'end_date' in item at index {idx} in {yaml_path}")
            
    return data
