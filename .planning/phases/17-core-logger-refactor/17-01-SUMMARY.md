---
phase: 17-core-logger-refactor
plan: 01
subsystem: Core Logging
tags: [logging, refactor, traceability]
dependency_graph:
  requires: []
  provides: [run-centric-logging]
  affects: [all-pipeline-components]
tech-stack:
  added: [JSONL]
  patterns: [Dual-File-Logging, Unified-Trace-Helper]
key-files:
  - src/logger.py
decisions:
  - Use dual-file logging (app.log for INFO+, debug.log for DEBUG+) to separate signal from noise.
  - Consolidate all structured traces (LLM API and decisions) into a single traces.jsonl file per run.
  - Implement a private helper _write_jsonl_trace to handle JSONL formatting and fallback directory creation.
metrics:
  duration: "Unknown"
  completed_date: "2026-07-07"
status: complete
---

# Phase 17 Plan 01: Core Logger Refactor Summary

Established a run-centric logging architecture that separates high-signal application logs from detailed debug traces and structured API logs.

## Changes Made

### 1. Dual-Log Separation
- Updated `setup_logging` to configure the root logger with two separate file handlers:
    - `app.log`: Restricted to `INFO` level and above.
    - `debug.log`: Captures all `DEBUG` level logs and above.
- Removed the automatic creation of `logs/traces/` and `logs/{run_id}/traces/` directories to simplify the filesystem structure.

### 2. Unified JSONL Trace Helper
- Implemented `_write_jsonl_trace(run_id, trace_type, payload)` as a central point for writing structured data.
- Ensures timestamps, trace types, and payloads are recorded in a machine-readable JSONL format in `traces.jsonl`.
- Handles fallback directory creation if `setup_logging` was not previously called.

### 3. Trace Logging Refactor
- Refactored `log_llm_api_call` and `log_decision_trace` to delegate all file writing logic to `_write_jsonl_trace`.
- Standardized the output to `traces.jsonl`, removing legacy individual JSON files for decisions.

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All tasks were verified with dedicated test scripts:
- `tests/verify_dual_logging.py`: Confirmed `app.log` (INFO+) and `debug.log` (DEBUG+) are created with correct filtering.
- `tests/verify_jsonl_trace.py`: Confirmed `_write_jsonl_trace` correctly appends valid JSONL and handles fallbacks.
- `tests/verify_trace_refactor.py`: Confirmed `log_llm_api_call` and `log_decision_trace` correctly write to `traces.jsonl`.

## Self-Check: PASSED
