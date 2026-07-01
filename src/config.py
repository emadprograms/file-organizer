"""Configuration management and API quota tracking for the File Categorizer application."""

import logging
import os
import sys
import time
import json
import yaml
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    """Application configuration holding API keys.
    
    Attributes:
        gemini_api_key (str): Primary API key for Gemini.
        openrouter_api_key (str): Fallback API key for OpenRouter.
        groq_api_key (str): Fallback API key for Groq.
    """
    gemini_api_key: str
    openrouter_api_key: str
    groq_api_key: str

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_ROOT / ".tracking"
LOG_FILE = TRACKING_DIR / "api_calls.log"
QUOTA_LIMIT = 1500
SECONDS_IN_24H = 24 * 60 * 60

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemma-4-26b-a4b-it")

def _get_recent_calls_count() -> int:
    """Calculate the number of API calls made within the last 24 hours.
    
    Reads from the local API call tracking log, purges older entries,
    and returns the count of recent calls.
    
    Returns:
        int: The number of API calls made in the last 24 hours.
    """
    if not LOG_FILE.exists():
        return 0
    
    current_time = time.time()
    recent_calls = 0
    valid_lines = []
    
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                timestamp = float(line)
                if current_time - timestamp <= SECONDS_IN_24H:
                    valid_lines.append(line)
                    recent_calls += 1
            except ValueError:
                continue
                
        if len(valid_lines) != len(lines):
            with open(LOG_FILE, "w") as f:
                if valid_lines:
                    f.write("\n".join(valid_lines) + "\n")
                else:
                    f.write("")
                
        return recent_calls
    except Exception:
        return 0

def load_config() -> AppConfig:
    """Load configuration from environment variables.
    
    Validates the presence of required API keys (Gemini) and checks for
    optional fallback keys (OpenRouter, Groq). Also reports on the remaining
    API quota for the current 24-hour period.
    
    Returns:
        AppConfig: The validated application configuration.
        
    Raises:
        SystemExit: If the required GEMINI_API_KEY is missing.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    
    missing_keys = []
    if not gemini_key:
        missing_keys.append("GEMINI_API_KEY")
        
    if missing_keys:
        logger.error(f"FATAL ERROR: Missing required API keys in environment: {', '.join(missing_keys)}")
        sys.exit(1)
        
    optional_missing = []
    if not openrouter_key:
        optional_missing.append("OPENROUTER_API_KEY")
    if not groq_key:
        optional_missing.append("GROQ_API_KEY")
        
    if optional_missing:
        logger.warning(f"The following optional fallback API keys are missing: {', '.join(optional_missing)}. Cloud failover may be limited.")
        
    TRACKING_DIR.mkdir(exist_ok=True)
    recent_calls = _get_recent_calls_count()
    remaining = max(0, QUOTA_LIMIT - recent_calls)
    
    logger.info(f"API Quota Remaining: {remaining}/{QUOTA_LIMIT} calls for the next 24h.")
    
    return AppConfig(
        gemini_api_key=gemini_key,
        openrouter_api_key=openrouter_key,
        groq_api_key=groq_key
    )

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
        print(f"Warning: Failed to record API call to quota log: {e}")



def setup_logging() -> None:
    """Configure application logging.
    
    Sets up a file handler in the project's 'logs' directory and a stream
    handler for standard error output. The log filename incorporates a timestamp.
    """
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_filename = f"{timestamp}_app.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / log_filename, encoding="utf-8"),
            logging.StreamHandler(sys.stderr)
        ]
    )


class InvalidConfigError(Exception):
    """Exception raised for invalid user configurations."""
    pass

def load_user_config(config_path: Path) -> 'UserConfig':
    from src.schemas import UserConfig
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
        return UserConfig(**data)
    except Exception as e:
        raise InvalidConfigError(f"Failed to load or validate config at {config_path}: {e}")
