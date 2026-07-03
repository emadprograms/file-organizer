import os
import sys
import json
import uuid
import logging
from datetime import datetime

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
_run_directories = {}

def setup_logging(run_id: str = None) -> str:
    """
    Provision a timestamped directory and configure logging.
    """
    if run_id is None:
        run_id = str(uuid.uuid4())[:8]
        
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dir_name = f"{timestamp}_{run_id}"
    full_dir = os.path.join(LOGS_DIR, dir_name)
    
    os.makedirs(full_dir, exist_ok=True)
    _run_directories[run_id] = full_dir
    
    # Setup standard logger
    logger = logging.getLogger("file_organizer")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to prevent duplicate logs during testing or repeated calls
    logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    log_file = os.path.join(full_dir, "app.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    return full_dir

def log_llm_api_call(request: dict, response: dict, run_id: str):
    """
    Append an LLM API request and response to llm_audit.jsonl.
    """
    log_dir = _run_directories.get(run_id)
    if not log_dir:
        # Fallback if log_llm_api_call is called without setup_logging
        log_dir = setup_logging(run_id)
        
    audit_file = os.path.join(log_dir, "llm_audit.jsonl")
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "request": request,
        "response": response
    }
    
    # Append as valid JSON line
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
