"""Configuration management and API quota tracking for the File Categorizer application."""

import os
import time
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRACKING_DIR = PROJECT_ROOT / ".tracking"
LOG_FILE = TRACKING_DIR / "api_calls.log"

logger = logging.getLogger(f"file_organizer.{__name__}")

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemma-4-31b-it")

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
