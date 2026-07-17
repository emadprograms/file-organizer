import os
import json
import shutil
import logging
from datetime import datetime
from src.utils.logger import setup_logging, _write_jsonl_trace

def test_jsonl_trace():
    run_id = "test_jsonl_trace"
    
    # Cleanup
    if os.path.exists("logs"):
        for d in os.listdir("logs"):
            if "test_jsonl_trace" in d:
                shutil.rmtree(os.path.join("logs", d))

    # Setup logging to ensure run directory exists in _run_directories
    run_dir = setup_logging(run_id=run_id)
    
    # Test data
    traces = [
        {"type": "llm_api", "payload": {"req": "hello", "res": "hi"}},
        {"type": "decision_route", "payload": {"route": "docs", "score": 0.9}},
        {"type": "decision_clean", "payload": {"action": "remove_headers", "count": 5}},
    ]

    for trace in traces:
        _write_jsonl_trace(trace["type"], trace["payload"])

    trace_file_path = os.path.join(run_dir, "traces.jsonl")
    
    assert os.path.exists(trace_file_path), "traces.jsonl should exist"
    
    with open(trace_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    assert len(lines) == len(traces), f"Expected {len(traces)} lines, found {len(lines)}"
    
    for i, line in enumerate(lines):
        data = json.loads(line)
        assert data["trace_type"] == traces[i]["type"], f"Line {i} type mismatch"
        assert data["payload"] == traces[i]["payload"], f"Line {i} payload mismatch"
        assert "timestamp" in data, f"Line {i} missing timestamp"

    # Test fallback directory creation
    run_id_fallback = "test_fallback_trace"
    # Clear the run directory cache just for this test if we could, 
    # but instead we just use a new ID that isn't in _run_directories.
    
    # We must force the fallback by clearing handlers and LogContext
    import logging
    from src.utils.logger import LogContext
    trace_logger = logging.getLogger("traces")
    trace_logger.handlers.clear()
    LogContext._instance = None
    
    _write_jsonl_trace("fallback_test", {"msg": "working"})
    
    # Find the directory created for the fallback
    found_dir = None
    if os.path.exists("logs"):
        fallback_dirs = [d for d in os.listdir("logs") if d.startswith("fallback_")]
        if fallback_dirs:
            # Sort to get the latest
            fallback_dirs.sort(reverse=True)
            found_dir = os.path.join("logs", fallback_dirs[0])
    
    assert found_dir is not None, "Fallback directory should have been created"
    assert os.path.exists(os.path.join(found_dir, "traces.jsonl")), "Fallback traces.jsonl should exist"

    print("Verification successful: _write_jsonl_trace works as expected, including fallback logic.")

if __name__ == "__main__":
    test_jsonl_trace()
