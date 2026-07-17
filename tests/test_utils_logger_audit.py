import os
import json
import pytest
import glob
import re
import logging

def get_all_python_files():
    return glob.glob("src/**/*.py", recursive=True)

def test_no_forbidden_prints():
    """
    Ensure no print() calls exist in src/, except for console.print().
    """
    forbidden_pattern = re.compile(r"(?<!console\.)\bprint\s*\(")
    violations = []
    
    for file_path in get_all_python_files():
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if forbidden_pattern.search(line):
                    violations.append(f"{file_path}:{line_num} -> {line.strip()}")
    
    if violations:
        msg = "Forbidden print() calls found: " + " | ".join(violations)
        pytest.fail(msg)

def test_canonical_logger_initialization():
    """
    Ensure loggers are initialized using: logging.getLogger(f"file_organizer.{__name__}")
    """
    logger_init_pattern = re.compile(r"logging\.getLogger\s*\((.*?)\)")
    required_pattern = 'f"file_organizer.{__name__}"'
    
    violations = []
    
    for file_path in get_all_python_files():
        if "logger.py" in file_path:
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            matches = logger_init_pattern.finditer(content)
            for match in matches:
                arg = match.group(1).strip()
                if arg != required_pattern:
                    violations.append(f"{file_path}: {arg}")
    
    if violations:
        msg = "Non-canonical logger initializations found: " + " | ".join(violations)
        pytest.fail(msg)

def test_jsonl_log_integrity():
    """
    Verify that log entries in debug.log are valid JSON.
    """
    from src.utils.logger import setup_logging
    
    # Setup logging to a temporary directory for the test
    log_dir = setup_logging(run_id="test_audit", verbose=True)
    debug_log_path = os.path.join(log_dir, "debug.log")
    
    # Trigger a log event
    test_logger = logging.getLogger("file_organizer")
    test_logger.debug("Integrity check trigger")
    
    if not os.path.exists(debug_log_path):
        pytest.fail(f"Log file {debug_log_path} was not created.")

    with open(debug_log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    if not lines:
        pytest.fail("Log file is empty.")

    violations = []
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError:
            violations.append(f"Line {line_num}: {line}")

    if violations:
        msg = "Invalid JSON entries found in " + debug_log_path + ": " + " | ".join(violations)
        pytest.fail(msg)
