"""Configuration management and API quota tracking for the File Categorizer application."""

import os
import time
import logging
from pathlib import Path
import yaml
from pydantic import BaseModel, Field
from src.core.exceptions import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRACKING_DIR = PROJECT_ROOT / ".tracking"
LOG_FILE = TRACKING_DIR / "api_calls.log"

logger = logging.getLogger(f"file_organizer.{__name__}")

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
ROUTING_MODEL = os.getenv("ROUTING_MODEL", "google/gemma-4-31b-it")

def record_successful_call() -> None:
    """Record a successful API call for quota tracking.
    
    Appends the current timestamp to the local tracking log file.
    Failures in recording do not crash the application but are printed as warnings.
    """
    TRACKING_DIR.mkdir(exist_ok=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.time()}\n")
    except Exception as e:
        logger.warning(f"Failed to record API call to quota log: {e}")

class AppConfig(BaseModel):
    """Application configuration structure."""
    inbox_path: str = Field(description="Path to the inbox directory")
    areas_root_path: str = Field(description="Path to the areas root directory")
    area_mappings: dict[str, str] = Field(default_factory=dict, description="Mapping of area names to area IDs")

    @classmethod
    def load(cls, path: Path | str) -> "AppConfig":
        """Load configuration from a YAML file.
        
        Args:
            path: Path to the configuration YAML file.
            
        Returns:
            AppConfig: Validated application configuration.
            
        Raises:
            ConfigurationError: If the YAML is malformed, invalid, or file is missing.
        """
        yaml_path = Path(path)
        
        if not yaml_path.exists():
            raise ConfigurationError(f"Configuration file not found: {yaml_path}")
            
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Malformed YAML in {yaml_path}: {e}") from e
            
        try:
            config = cls(**data)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration data in {yaml_path}: {e}") from e
            
        inbox = Path(config.inbox_path)
        areas = Path(config.areas_root_path)
        
        try:
            inbox.mkdir(parents=True, exist_ok=True)
            areas.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(f"Failed to create structural directories: {e}") from e
            
        return config
