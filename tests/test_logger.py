import sys
import os
import json
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from logger import setup_logging, log_llm_api_call

def test_setup_logging(tmp_path, monkeypatch):
    # Mock the logs directory to point to tmp_path
    monkeypatch.setattr("logger.LOGS_DIR", str(tmp_path))
    
    # Clear handlers so setup_logging creates new ones
    logging.getLogger().handlers.clear()
    
    # Run setup
    log_dir = setup_logging(run_id="test_run_123")
    
    # Assert directory exists
    assert os.path.exists(log_dir)
    assert "test_run_123" in log_dir
    
    # Check if we can log
    logger = logging.getLogger("file_organizer")
    logger.info("Test message 123")
    
    # Assert log file is created and written in UTF-8
    app_log = os.path.join(log_dir, "app.log")
    assert os.path.exists(app_log)
    with open(app_log, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Test message 123" in content

def test_log_llm_api_call(tmp_path, monkeypatch):
    monkeypatch.setattr("logger.LOGS_DIR", str(tmp_path))
    
    # Need to setup logging first to create the directory for the run_id
    run_id = "test_llm_123"
    log_dir = setup_logging(run_id=run_id)
    
    req = {"prompt": "hello", "arabic": "مرحبا"}
    res = {"text": "world", "arabic": "عالم"}
    
    log_llm_api_call(req, res, run_id)
    
    audit_file = os.path.join(log_dir, "llm_audit.jsonl")
    assert os.path.exists(audit_file)
    
    with open(audit_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["request"]["prompt"] == "hello"
        assert data["response"]["arabic"] == "عالم"

def test_setup_logging_no_run_id(tmp_path, monkeypatch):
    monkeypatch.setattr("logger.LOGS_DIR", str(tmp_path))
    log_dir = setup_logging()
    assert os.path.exists(log_dir)
    assert "_" in os.path.basename(log_dir) # Timestamp has underscore

def test_log_decision_trace(tmp_path, monkeypatch):
    monkeypatch.setattr("logger.LOGS_DIR", str(tmp_path))
    
    # Setup logging to create the run directory
    run_id = "test_trace_123"
    log_dir = setup_logging(run_id=run_id)
    
    decision_type = "routing"
    # Added Arabic text to verify ensure_ascii=False
    payload = {"category": "forms", "selected": "1_requests", "reason": "سبب التوجيه العربي"}
    
    from logger import log_decision_trace
    log_decision_trace(decision_type, payload, run_id)
    
    # The utility creates a 'traces' subdirectory
    traces_dir = os.path.join(log_dir, "traces")
    assert os.path.exists(traces_dir)
    
    # Find the file (timestamped)
    files = os.listdir(traces_dir)
    assert len(files) == 1
    filename = files[0]
    assert filename.startswith("routing") or "routing" in filename
    
    file_path = os.path.join(traces_dir, filename)
    
    # Verify ensure_ascii=False by reading raw file text
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
        assert "سبب التوجيه العربي" in raw_text
        assert "\\u" not in raw_text  # Make sure no unicode escapes
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data == payload

