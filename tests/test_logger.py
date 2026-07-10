import os
import json
import logging
import pytest
from unittest.mock import patch
from src.logger import LogContext, JSONLFormatter, setup_logging, log_decision_trace

@pytest.fixture(autouse=True)
def reset_log_context():
    """Resets the LogContext singleton before each test."""
    LogContext._instance = None

def test_log_context_singleton():
    """Verify LogContext is a singleton and maintains state."""
    ctx1 = LogContext.get_instance()
    ctx2 = LogContext.get_instance()
    assert ctx1 is ctx2
    
    ctx1.initialize("test_dir", "test_id")
    assert ctx2.run_dir == "test_dir"
    assert ctx2.run_id == "test_id"

def test_log_context_init_restriction():
    """Verify that LogContext cannot be instantiated directly."""
    LogContext.get_instance() # Ensure instance exists
    with pytest.raises(RuntimeError, match="Use LogContext.get_instance"):
        LogContext()

def test_jsonl_formatter():
    """Verify JSONLFormatter produces valid JSON with required keys."""
    formatter = JSONLFormatter()
    logger = logging.getLogger("test_logger")
    record = logger.makeRecord(
        name="test_logger", 
        level=logging.INFO, 
        fn="test_file.py", 
        lno=10, 
        msg="Test message", 
        args=None, 
        exc_info=None
    )
    
    formatted_json = formatter.format(record)
    data = json.loads(formatted_json)
    
    required_keys = {"timestamp", "level", "name", "message", "filename", "lineno"}
    assert required_keys.issubset(data.keys())
    assert data["message"] == "Test message"
    assert data["name"] == "test_logger"
    assert data["level"] == "INFO"

def test_setup_logging_basic(tmp_path):
    """Verify setup_logging initializes context and creates log files."""
    with patch("src.logger.LOGS_DIR", str(tmp_path)):
        run_id = "test_run"
        run_dir = setup_logging(run_id=run_id, verbose=False)
        
        # Verify LogContext
        ctx = LogContext.get_instance()
        assert ctx.run_id == run_id
        assert ctx.run_dir == run_dir
        
        # Verify files created
        assert os.path.exists(os.path.join(run_dir, "app.log"))
        assert os.path.exists(os.path.join(run_dir, "debug.log"))

def test_setup_logging_noise_suppression_blacklist(tmp_path):
    """Verify permissive blacklist when verbose=False."""
    with patch("src.logger.LOGS_DIR", str(tmp_path)):
        setup_logging(verbose=False)
        
        # Blacklisted libraries should be WARNING
        for library in ["openai", "google_genai", "urllib3", "httpcore"]:
            assert logging.getLogger(library).level == logging.WARNING
            
        # Root should be DEBUG
        assert logging.getLogger().level == logging.DEBUG

def test_setup_logging_noise_suppression_whitelist(tmp_path):
    """Verify strict whitelist when verbose=True."""
    with patch("src.logger.LOGS_DIR", str(tmp_path)):
        setup_logging(verbose=True)
        
        # Root should be WARNING
        assert logging.getLogger().level == logging.WARNING
        # file_organizer should be DEBUG
        assert logging.getLogger("file_organizer").level == logging.DEBUG
        
        # Any other library should effectively be WARNING (inherited from root)
        assert logging.getLogger("some_random_lib").level == logging.NOTSET # NOTSET inherits WARNING from root

def test_log_decision_trace(tmp_path):
    """Verify structured trace logging."""
    with patch("src.logger.LOGS_DIR", str(tmp_path)):
        # Initialize context first
        run_id = "trace_run"
        run_dir = setup_logging(run_id=run_id)
        
        payload = {"decision": "A", "reason": "B"}
        log_decision_trace("test_type", payload)
        
        trace_file = os.path.join(run_dir, "traces.jsonl")
        assert os.path.exists(trace_file)
        
        with open(trace_file, "r", encoding="utf-8") as f:
            line = f.readline()
            data = json.loads(line)
            assert data["trace_type"] == "decision_test_type"
            assert data["payload"] == payload

def test_log_decision_trace_fallback(tmp_path):
    """Verify fallback directory behavior when called before setup_logging."""
    LogContext._instance = None # Ensure no context
    with patch("src.logger.LOGS_DIR", str(tmp_path)):
        payload = {"decision": "fallback"}
        log_decision_trace("fallback_type", payload)
        
        # Check if a fallback directory was created in LOGS_DIR
        entries = os.listdir(tmp_path)
        fallback_dirs = [e for e in entries if e.startswith("fallback_")]
        assert len(fallback_dirs) == 1
        
        # Verify the content
        trace_file = os.path.join(tmp_path, fallback_dirs[0], "traces.jsonl")
        assert os.path.exists(trace_file)
        
        with open(trace_file, "r", encoding="utf-8") as f:
            line = f.readline()
            data = json.loads(line)
            assert data["trace_type"] == "decision_fallback_type"

def test_hierarchical_logger_naming():
    """Verify that sample modules in src/ use the standard logger naming and variable."""
    import importlib
    
    # Sample of modules to check
    modules_to_check = [
        "src.organize",
        "src.core.config",
        "src.core.ui",
        "src.llm.llm",
        "src.processing.pipeline",
    ]
    
    for mod_name in modules_to_check:
        mod = importlib.import_module(mod_name)
        
        # Verify variable name is 'logger'
        assert hasattr(mod, "logger"), f"Module {mod_name} is missing the 'logger' variable"
        
        # Verify logger name matches hierarchical pattern
        logger = getattr(mod, "logger")
        # The actual __name__ will be 'src.module', so logger name will be 'file_organizer.src.module'
        expected_name = f"file_organizer.{mod_name}"
        assert logger.name == expected_name, f"Module {mod_name} logger name {logger.name} does not match expected {expected_name}"

