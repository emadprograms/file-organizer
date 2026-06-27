import os
import sys
import time
from pathlib import Path
from dataclasses import dataclass

@dataclass
class AppConfig:
    gemini_api_key: str
    openrouter_api_key: str
    groq_api_key: str

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_ROOT / ".tracking"
LOG_FILE = TRACKING_DIR / "api_calls.log"
QUOTA_LIMIT = 1500
SECONDS_IN_24H = 24 * 60 * 60

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "gemma-4-26b-a4b-it")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen3.6-27b")

def _get_recent_calls_count() -> int:
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
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    
    missing_keys = []
    if not gemini_key:
        missing_keys.append("GEMINI_API_KEY")
    if not openrouter_key:
        missing_keys.append("OPENROUTER_API_KEY")
    if not groq_key:
        missing_keys.append("GROQ_API_KEY")
        
    if missing_keys:
        print(f"FATAL ERROR: Missing required API keys in environment: {', '.join(missing_keys)}")
        sys.exit(1)
        
    TRACKING_DIR.mkdir(exist_ok=True)
    recent_calls = _get_recent_calls_count()
    remaining = max(0, QUOTA_LIMIT - recent_calls)
    
    print(f"API Quota Remaining: {remaining}/{QUOTA_LIMIT} calls for the next 24h.")
    
    return AppConfig(
        gemini_api_key=gemini_key,
        openrouter_api_key=openrouter_key,
        groq_api_key=groq_key
    )

def record_successful_call() -> None:
    TRACKING_DIR.mkdir(exist_ok=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.time()}\n")
    except Exception as e:
        print(f"Warning: Failed to record API call to quota log: {e}")

