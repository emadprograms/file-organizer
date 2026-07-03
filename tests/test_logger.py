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
