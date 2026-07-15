import yaml
from pathlib import Path
import logging
from src.core.exceptions import ConfigurationError

logger = logging.getLogger(f"file_organizer.{__name__}")

def load_tenant_config(target_dir: Path) -> list[str]:
    """
    Loads tenant names from a tenants.yaml file located in the target directory.
    
    Args:
        target_dir (Path): The directory where tenants.yaml is expected.
        
    Returns:
        list[str]: A list of primary tenant names.
        
    Raises:
        ConfigurationError: If the YAML file is malformed or missing the 'tenants' key.
    """
    yaml_path = target_dir / "tenants.yaml"
    
    if not yaml_path.exists():
        logger.warning(f"No tenants.yaml found in {target_dir}. Falling back to empty tenant list.")
        return []
        
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Malformed YAML in {yaml_path}: {e}") from e
        
    if not isinstance(data, dict) or "tenants" not in data:
        raise ConfigurationError(f"Missing 'tenants' key in {yaml_path}")
        
    tenants = data.get("tenants")
    if not isinstance(tenants, list):
        raise ConfigurationError(f"'tenants' must be a list of strings in {yaml_path}")
        
    # Ensure all elements are strings
    return [str(t) for t in tenants]
