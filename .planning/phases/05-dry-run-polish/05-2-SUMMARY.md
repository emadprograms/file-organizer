---
phase: "05"
plan: "2"
subsystem: testing
tags: [e2e, unit-tests, dry-run, error-handling, llm-retry]
dependency_graph:
  requires: [05-1-PLAN.md]
  provides: [e2e-test-suite, edge-case-coverage]
  affects: [tests/test_e2e.py, tests/test_cli.py, tests/test_pipeline.py, tests/test_llm.py]
tech_stack:
  added: [subprocess E2E testing, fixture isolation pattern]
  patterns: [pre-baked checkpoint fixtures, bytes decode with errors=replace]
key_files:
  created:
    - tests/test_e2e.py
    - tests/fixtures/golden_1273/1273_categorized.pdf
  modified:
    - tests/test_cli.py
    - tests/test_pipeline.py
    - tests/test_llm.py
    - requirements.txt
decisions:
  - "E2E test uses pre-baked cleaned.json and grouped.json checkpoints to bypass LLM calls entirely"
  - "subprocess.run with bytes output + decode(utf-8, errors=replace) for Windows cp1252 safety"
  - "Malformed JSON test uses a real subprocess invocation (not mocks) to verify true CLI behavior"
  - "LLM retry test asserts call_count <= 6 (Gemini max) to verify bounded-not-infinite retry"
metrics:
  duration: "~30 minutes"
  completed: "2026-07-05"
  tasks_completed: 4
  files_modified: 5
status: complete
---

# Phase 05 Plan 2: End-to-End Tests & Polish Summary

**One-liner:** Isolated E2E dry-run test + 3 targeted edge-case tests covering missing JSON, malformed JSON, and LLM 500 retry limits

## What Was Built

### Task 1 — `test_dry_run_end_to_end` in `tests/test_e2e.py`
- Created `tests/fixtures/golden_1273/1273_categorized.pdf` — minimal 1-page PDF via PyMuPDF
- E2E test uses `_setup_dry_run_dir()` to create an isolated house directory in `tmp_path`
- Injects pre-baked `cleaned.json` and `grouped.json` checkpoints so no LLM API calls are made
- Runs `python -m src.organize ... --dry-run` via `subprocess.run` as a real CLI invocation
- Asserts: `returncode == 0`, rich output contains expected identifiers, no output PDFs created, no manifest written, checkpoints preserved
- Fixed Windows encoding: bytes output decoded with `utf-8, errors=replace` to handle rich box-drawing chars in cp1252 terminals
- Commit: `133bf12`

### Task 2 — `test_validate_target_directory_missing_json` in `tests/test_cli.py`
- Provides a PDF but no `_report.json`; verifies graceful `sys.exit(1)` with correct error message
- Commit: `1c92174`

### Task 3 — `test_malformed_json_graceful_failure` in `tests/test_pipeline.py`
- Creates a directory with a syntactically invalid `_report.json` (`{invalid json: !@#`)
- Runs full CLI via subprocess; verifies non-zero exit and JSON-related error in stderr
- Commit: `1c92174`

### Task 4 — `test_llm_500_max_retries_halts` in `tests/test_llm.py`
- All three providers (Gemini, OpenRouter, Groq) raise `Exception("500 Internal Server Error")` on every call
- Verifies `RuntimeError("LLM routing failed across all providers")` is raised
- Asserts `mock_gemini.call_count <= 6` to prove retry loop is bounded, not infinite
- Commit: `1c92174`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] `rich` not installed in venv**
- **Found during:** E2E test run
- **Issue:** `ModuleNotFoundError: No module named 'rich'` when subprocess invoked the visualizer
- **Fix:** `pip install rich`; also added `rich` and `rapidfuzz` (also missing) to `requirements.txt`
- **Files modified:** `requirements.txt`
- **Commit:** `133bf12`

**2. [Rule 1 - Bug] Windows cp1252 encoding crash in subprocess capture**
- **Found during:** E2E test run (second attempt after rich install)
- **Issue:** `text=True` in subprocess.run uses system encoding (cp1252 on Windows); rich's box-drawing characters (0x90 etc.) cause `UnicodeDecodeError` making `result.stdout` → `None`
- **Fix:** Use `capture_output=True` without `text=True`, then decode bytes manually with `utf-8, errors=replace`
- **Files modified:** `tests/test_e2e.py`
- **Commit:** `133bf12`

## Verification

- `pytest tests/test_e2e.py` — 1 passed ✅
- `pytest tests/test_cli.py::test_validate_target_directory_missing_json` — passed ✅
- `pytest tests/test_pipeline.py::test_malformed_json_graceful_failure` — passed ✅
- `pytest tests/test_llm.py::test_llm_500_max_retries_halts` — passed ✅

## Self-Check: PASSED

- [x] `tests/test_e2e.py` exists with `test_dry_run_end_to_end`
- [x] `tests/fixtures/golden_1273/1273_categorized.pdf` exists
- [x] `test_validate_target_directory_missing_json` in `tests/test_cli.py`
- [x] `test_malformed_json_graceful_failure` in `tests/test_pipeline.py`
- [x] `test_llm_500_max_retries_halts` in `tests/test_llm.py`
- [x] All 4 new tests pass (verified 2026-07-05)
