# Phase 04 Summary: Logging Infrastructure Refactor

## Objective
Establish an isolated, unified, and structured logging system to eliminate third-party noise and provide a consistent run context.

## Changes
### `src/logger.py`
- **Implemented `LogContext` Singleton**: Replaced the global `_run_directories` dictionary with a singleton that centrally manages `run_dir` and `run_id`.
- **Implemented `JSONLFormatter`**: Created a custom formatter that outputs log records as JSON strings, ensuring machine-readability for debug logs.
- **Refactored `setup_logging`**:
    - Initializes `LogContext` at startup.
    - Configures `app.log` as plain text (INFO+).
    - Configures `debug.log` using `JSONLFormatter` (DEBUG+).
    - Implemented Noise Suppression:
        - `verbose=False`: Blocks `openai`, `google-genai`, `urllib3`, and `httpcore` using a permissive blacklist.
        - `verbose=True`: Blocks ALL except the `file_organizer` hierarchy using a strict whitelist.
- **Updated Trace Logging**: Modified `_write_jsonl_trace` and `log_decision_trace` to use `LogContext` for directory resolution, removing the need to pass `run_id` through the pipeline.

## Verification Results
- **LogContext**: Verified as a true singleton via `verify_log_context.py`.
- **JSONL Format**: Verified that `debug.log` output matches the required schema via `verify_jsonl_formatter.py` and E2E run.
- **Noise Suppression**: Verified both whitelist and blacklist modes via `verify_setup_logging.py`.
- **Trace Logging**: Verified that decisions are correctly written to `traces.jsonl` using the singleton context via `verify_trace_logging.py`.
- **Integration**: Verified that `src/organize.py` correctly triggers the new logging setup.

## Outcomes
- `debug.log` is now a machine-readable JSONL file.
- Third-party library noise is suppressed based on the `verbose` flag.
- Run context is unified, eliminating redundant `run_id` passing.
- Trace logs are decoupled from manual ID management.
