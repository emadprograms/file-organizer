from typing import Any
import os
import shutil
import json
from src.utils.logger import setup_logging, log_decision_trace, _write_jsonl_trace

def test_trace_refactor() -> None:
    """
    Test trace refactor.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    run_id = "test_trace_refactor"
    
    # Cleanup
    if os.path.exists("logs"):
        for d in os.listdir("logs"):
            if "test_trace_refactor" in d:
                shutil.rmtree(os.path.join("logs", d))

    run_dir = setup_logging(run_id=run_id)
    
    # Test LLM API call logging via _write_jsonl_trace
    req = {"prompt": "hello"}
    res = {"text": "hi"}
    _write_jsonl_trace("llm_api", {"request": req, "response": res})
    
    # Test decision trace logging
    payload = {"decision": "route_to_pdf", "score": 0.8}
    log_decision_trace("routing", payload)
    
    trace_file_path = os.path.join(run_dir, "traces.jsonl")
    
    assert os.path.exists(trace_file_path), "traces.jsonl should exist"
    
    with open(trace_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    assert len(lines) == 2, f"Expected 2 trace lines, found {len(lines)}"
    
    # Line 1: LLM API
    data1 = json.loads(lines[0])
    assert data1["trace_type"] == "llm_api"
    assert data1["payload"]["request"] == req
    assert data1["payload"]["response"] == res
    
    # Line 2: Decision
    data2 = json.loads(lines[1])
    assert data2["trace_type"] == "decision_routing"
    assert data2["payload"] == payload

    print("Verification successful: Trace logging functions now correctly delegate to _write_jsonl_trace.")

if __name__ == "__main__":
    test_trace_refactor()
