# Phase 1: Foundation & Infrastructure - Pattern Mapping

## Overview
This phase represents a greenfield setup for the File Organizer project. As noted in the `CONTEXT.md` decisions, there are no existing reusable assets or codebase analogs to build from.

## Files to Create

### 1. `organize.py` (or `main.py`)
- **Role:** CLI Entry Point and Startup Validation
- **Data Flow:** 
  - Receives CLI arguments (`directory_path`, `--model` flag).
  - Validates environment (`GEMINI_API_KEY`).
  - Validates target directory state (ensures presence of `[ID]_categorized.pdf` and `[ID]_report.json`).
  - Provisions `output` subdirectory.
- **Existing Analog:** N/A (Greenfield)
- **Code Excerpts:** N/A

### 2. `llm_client.py`
- **Role:** Centralized LLM API Intermediary
- **Data Flow:**
  - Manages requests to `google-genai` SDK.
  - Enforces synchronous 7-second rate limits between calls.
  - Intercepts error responses (400, 404, 429, 500) and orchestrates specific retry and backoff counters.
  - Shrinks chunk sizes or skips on repeated 500 errors.
- **Existing Analog:** N/A (Greenfield)
- **Code Excerpts:** N/A

### 3. `logger.py`
- **Role:** Application Logging & LLM Auditing
- **Data Flow:**
  - Sets up plain text logging to `./logs/[YYYY-MM-DD_HHMMSS]/` mirroring CLI stdout.
  - Exposes dedicated channels/methods to log LLM API request and response payloads to a separate `JSONL` file.
  - Enforces `utf-8` encoding for all operations.
- **Existing Analog:** N/A (Greenfield)
- **Code Excerpts:** N/A

### 4. `fs_utils.py`
- **Role:** Safe Filesystem Operations
- **Data Flow:**
  - Receives desired path/filename strings.
  - Applies Unicode `NFC` normalization and strips Windows reserved chars / invisible control chars.
  - Truncates filenames to 200 characters.
  - Exposes context managers or functions for atomic writes (write to `.tmp` -> `rename`).
- **Existing Analog:** N/A (Greenfield)
- **Code Excerpts:** N/A

### 5. `tests/` Directory Structure
- **Role:** Unit and integration testing matching the Nyquist validation gate constraints.
- **Files Expected:** `test_cli.py`, `test_llm_client.py`, `test_logger.py`, `test_fs_utils.py`
- **Existing Analog:** N/A (Greenfield)
- **Code Excerpts:** N/A
