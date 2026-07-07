import os
import sys
import json
import uuid
import logging
from datetime import datetime

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
_run_directories = {}

def setup_logging(run_id: str = None, verbose: bool = False) -> str:
    """
    Provision a timestamped directory and configure logging.
    """
    if run_id is None:
        run_id = str(uuid.uuid4())[:8]
        
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dir_name = f"{timestamp}_{run_id}"
    full_dir = os.path.join(LOGS_DIR, dir_name)
    
    os.makedirs(full_dir, exist_ok=True)
    log_dir = full_dir
    _run_directories[run_id] = full_dir
    
    # Setup standard logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Check if handlers already exist to prevent duplicate logs or overriding other handlers
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # App log - INFO level and above
        app_log_file = os.path.join(full_dir, "app.log")
        app_handler = logging.FileHandler(app_log_file, encoding='utf-8')
        app_handler.setFormatter(formatter)
        app_handler.setLevel(logging.INFO)
        logger.addHandler(app_handler)

        # Debug log - DEBUG level and above
        debug_log_file = os.path.join(full_dir, "debug.log")
        debug_handler = logging.FileHandler(debug_log_file, encoding='utf-8')
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)
        logger.addHandler(debug_handler)
        
        # Stream handler
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        if verbose:
            stream_handler.setLevel(logging.DEBUG)
        else:
            stream_handler.setLevel(logging.INFO)
        logger.addHandler(stream_handler)
    
    return full_dir

def _write_jsonl_trace(run_id: str, trace_type: str, payload: dict):
    """
    Write a structured JSON trace to traces.jsonl in the run directory.
    """
    log_dir = _run_directories.get(run_id)
    if not log_dir:
        # Fallback if _write_jsonl_trace is called without setup_logging
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        dir_name = f"{timestamp}_{run_id}"
        log_dir = os.path.join(LOGS_DIR, dir_name)
        os.makedirs(log_dir, exist_ok=True)
        _run_directories[run_id] = log_dir
        
    trace_file = os.path.join(log_dir, "traces.jsonl")
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "trace_type": trace_type,
        "payload": payload
    }
    
    with open(trace_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def log_llm_api_call(request: dict, response: dict, run_id: str):
    """
    Append an LLM API request and response to traces.jsonl.
    """
    payload = {
        "request": request,
        "response": response
    }
    _write_jsonl_trace(run_id, "llm_api", payload)

def log_decision_trace(decision_type: str, payload: dict, run_id: str = None):
    """
    Append a structured JSON audit log for a pipeline decision to traces.jsonl.
    """
    _write_jsonl_trace(run_id, f"decision_{decision_type}", payload)

