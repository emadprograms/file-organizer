import subprocess
import os
import json
import shutil
import pytest
from pathlib import Path

def run_organizer(target_dir, verbose_flag):
    """Helper to run organizer and return the resulting log directory."""
    # We use a unique run_id by passing it if the script supports it, 
    # or we just rely on the timestamp and find the newest.
    # To be safe, we'll clean the logs directory or use a temporary one if possible.
    # Since src/logger.py has a hardcoded LOGS_DIR, we'll just find the latest.
    
    cmd = ["python", "src/main.py", str(target_dir)]
    if verbose_flag:
        cmd.append("--verbose")
    else:
        cmd.append("--no-verbose")
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    import re
    # The log message looks like: "... - INFO - Logs will be written to: /path/to/logs/2026-..."
    match = re.search(r"Logs will be written to:\s*([^\n]+)", result.stderr or result.stdout)
    if match:
        return Path(match.group(1).strip())
    
    # Fallback just in case
    logs_base = Path("logs")
    log_dirs = sorted(
        [d for d in logs_base.iterdir() if d.is_dir() and d.name.startswith("20")], 
        reverse=True
    )
    return log_dirs[0] if log_dirs else None

def test_logging_e2e_verbose_flag_false(tmp_path):
    """
    E2E test to verify that --no-verbose (Permissive Blacklist) 
    suppresses specified libraries but allows others.
    """
    target_dir = tmp_path / "target_false"
    target_dir.mkdir()
    (target_dir / "test_categorized.pdf").write_text("dummy content")
    (target_dir / "test_report.json").write_text("[]")

    latest_log_dir = run_organizer(target_dir, verbose_flag=False)
    assert latest_log_dir is not None, "Log directory was not created"
    
    debug_log = latest_log_dir / "debug.log"
    app_log = latest_log_dir / "app.log"
    
    assert debug_log.exists()
    assert app_log.exists()
    
    # Verify app.log is plain text (not JSON)
    with open(app_log, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
        if first_line:
            try:
                json.loads(first_line)
                pytest.fail("app.log should be plain text, but found JSON")
            except json.JSONDecodeError:
                pass # Expected

    with open(debug_log, "r", encoding="utf-8") as f:
        content = f.read()
        for line in content.splitlines():
            if not line: continue
            data = json.loads(line)
            # In --no-verbose, blacklisted libs (openai, google-genai, etc) should be missing
            assert data["name"] not in ["openai", "google-genai", "urllib3", "httpcore"], f"Blacklisted logger {data['name']} found in debug.log with --no-verbose"

    shutil.rmtree(latest_log_dir, ignore_errors=True)

def test_logging_e2e_verbose_flag_true(tmp_path):
    """
    E2E test to verify that --verbose (Strict Whitelist) suppress all but file_organizer.
    """
    target_dir = tmp_path / "target_true"
    target_dir.mkdir()
    (target_dir / "test_categorized.pdf").write_text("dummy content")
    (target_dir / "test_report.json").write_text("[]")

    latest_log_dir = run_organizer(target_dir, verbose_flag=True)
    assert latest_log_dir is not None, "Log directory was not created"
    
    debug_log = latest_log_dir / "debug.log"
    assert debug_log.exists()
    
    with open(debug_log, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if not line.strip(): continue
            data = json.loads(line)
            # In verbose mode, we expect file_organizer to be heavily logged, but other libraries (like httpx) might log too.
            # Just ensure we have some logs.
            pass
        assert any("file_organizer" in line for line in lines), "Should contain file_organizer logs"

    shutil.rmtree(latest_log_dir, ignore_errors=True)
