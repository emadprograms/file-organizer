import os
import sys
import json
import uuid
import logging
from datetime import datetime

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))

class LogContext:
    """
    Singleton to manage the current run context (run_dir and run_id).
    """
    _instance = None

    def __init__(self):
        if LogContext._instance is not None:
            raise RuntimeError("Use LogContext.get_instance() instead of constructor")
        self.run_dir = None
        self.run_id = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self, run_dir: str, run_id: str):
        """
        Sets the context once at startup.
        """
        self.run_dir = run_dir
        self.run_id = run_id

class JSONLFormatter(logging.Formatter):
    """
    Formatter that outputs log records as JSON strings (JSONL).
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack_trace"] = self.formatStack(record.stack_info)
            
        return json.dumps(log_record, ensure_ascii=False)

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
    
    # Initialize LogContext singleton
    LogContext.get_instance().initialize(full_dir, run_id)
    
    # Setup root logger
    root_logger = logging.getLogger()
    
    # Reset handlers to avoid duplication on re-initialization
    if root_logger.hasHandlers():
        for handler in root_logger.handlers:
            handler.close()
        root_logger.handlers.clear()

    # Configuration based on verbose flag (Decision D-03)
    if verbose:
        # Strict Whitelist: Root WARNING, only file_organizer DEBUG
        root_logger.setLevel(logging.WARNING)
        logging.getLogger("file_organizer").setLevel(logging.DEBUG)
    else:
        # Permissive Blacklist: Root DEBUG, block noisy libraries
        root_logger.setLevel(logging.DEBUG)
        for library in ["openai", "google_genai", "google_genai.models", "urllib3", "httpcore"]:
            logging.getLogger(library).setLevel(logging.WARNING)
    
    # Formatters
    text_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    jsonl_formatter = JSONLFormatter()
    
    # App log - INFO level and above (Plain Text)
    app_log_file = os.path.join(full_dir, "app.log")
    app_handler = logging.FileHandler(app_log_file, encoding='utf-8')
    app_handler.setFormatter(text_formatter)
    app_handler.setLevel(logging.INFO)
    root_logger.addHandler(app_handler)

    # Debug log - DEBUG level and above (JSONL)
    debug_log_file = os.path.join(full_dir, "debug.log")
    debug_handler = logging.FileHandler(debug_log_file, encoding='utf-8')
    debug_handler.setFormatter(jsonl_formatter)
    debug_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(debug_handler)
    
    # Stream handler
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except (AttributeError, OSError) as e:
            root_logger.debug(f"Failed to reconfigure stdout to utf-8: {e}")
            
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(text_formatter)
    stream_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    root_logger.addHandler(stream_handler)
    
    return full_dir

def _write_jsonl_trace(trace_type: str, payload: dict):
    """
    Write a structured JSON trace to traces.jsonl in the run directory.
    """
    ctx = LogContext.get_instance()
    log_dir = ctx.run_dir
    
    if not log_dir:
        # Fallback if _write_jsonl_trace is called without setup_logging
        # We cannot reasonably recover the run_id here without it being passed,
        # so we create a fallback directory.
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        dir_name = f"fallback_{timestamp}"
        log_dir = os.path.join(LOGS_DIR, dir_name)
        os.makedirs(log_dir, exist_ok=True)
        ctx.initialize(log_dir, "fallback")
        
    trace_file = os.path.join(log_dir, "traces.jsonl")
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "trace_type": trace_type,
        "payload": payload
    }
    
    with open(trace_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_decision_trace(decision_type: str, payload: dict):
    """
    Append a structured JSON audit log for a pipeline decision to traces.jsonl.
    """
    _write_jsonl_trace(f"decision_{decision_type}", payload)

