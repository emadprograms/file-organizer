# Phase 1: Foundation & Infrastructure - Research

## Executive Summary
This phase focuses on building the core scaffolding and shared utilities of the File Organizer CLI. It does not implement any document parsing or LLM-based categorization logic, but establishes the essential primitives that Pass 1 and Pass 2 will rely upon. Key focus areas include CLI argument parsing, startup validation, robust LLM API interactions with specific retry/rate-limiting logic, logging infrastructure, and safe filesystem operations handling Arabic filenames.

## What do I need to know to PLAN this phase well?

### 1. CLI and Startup Validation (INIT-01 to INIT-07)
*   **CLI Framework**: Use Python's built-in `argparse` as the CLI surface is simple (a single directory path argument and a `--model` flag).
*   **Expected State**: 
    *   Command looks like: `python organize.py ./pdfs/1273`
    *   Target directory must contain exactly:
        *   `[ID]_categorized.pdf` (from which the house ID, e.g., 1273, is derived)
        *   `[ID]_report.json`
    *   `GEMINI_API_KEY` must exist in the environment (`python-dotenv` can be used to load it).
*   **Outputs**: An `output` subdirectory should be provisioned inside the target directory.

### 2. LLM Client Architecture (LLM-01 to LLM-09)
*   **Library**: The official `google-genai` SDK is required (legacy `google-generativeai` must not be used).
*   **Model Config**: Default to `gemma-4-26b-a4b-it`. Switchable to `gemma-4-31b-it` via CLI flag. All API calls must route through a single, centralized client class.
*   **Rate Limiting**: Strictly synchronous execution. Must enforce a 7-second minimum interval between API requests (token bucket or simple `time.sleep` mechanism).
*   **Error Handling and Retries**:
    *   **400/404**: Fail fast, abort entirely.
    *   **500**: Wait 15 seconds, retry.
    *   **429**: Wait 65 seconds, retry. Fail after 3 consecutive 429s.
    *   **Context-Specific 500 Handling**:
        *   Boundary calls: shrink chunk size after 5 consecutive 500s; fail at 10.
        *   Other calls: skip after 5 consecutive 500s, log warning.
    *   **State**: Error counters reset on any successful response. `tenacity` is recommended for structured retry logic, but stateful counter management needs to be carefully orchestrated to adhere to these rules.

### 3. Logging & Audit (LOG-01 to LOG-03)
*   **Location**: `./logs/[YYYY-MM-DD_HHMMSS]/`
*   **Format**: 
    *   Plain text logs (`logging` module) mimicking CLI print statements.
    *   A separate `JSONL` format specifically for LLM API requests and responses (audit trail).
*   **Encoding**: All logs must strictly use `utf-8` due to the prevalence of Arabic text.

### 4. Filesystem Utilities (FS-01 to FS-04)
*   **Path Constraints**: Truncate filenames to 200 characters to prevent `MAX_PATH` errors on Windows.
*   **Arabic Text Normalization**: Files/folders need to be stripped of Windows reserved characters and invisible Unicode control characters. All paths should be normalized using Unicode `NFC` normalization.
*   **Atomic Writes**: Guaranteed via writing files to a `.tmp` extension in the target directory, then performing an atomic rename to the final filename (avoids cross-device link errors and partial writes).

## Validation Architecture

To pass the Nyquist validation gate and ensure robustness for downstream phases, the following testing constraints and coverage checks must be instituted:

1.  **CLI & Init Coverage**:
    *   Assert failure codes and standard error outputs when missing `GEMINI_API_KEY`, target `.pdf`, or target `.json`.
    *   Verify the accurate extraction of the house ID from valid and edge-case filenames.
2.  **LLM Client Resiliency**:
    *   **Mocked Interactions**: Use `unittest.mock` to simulate `google-genai` API responses.
    *   **Rate Limit Verification**: Assert that sequential API calls measure $\ge$ 7 seconds between executions.
    *   **Retry Logic Assertions**: Verify that a 400 response immediately raises an exception. Ensure 429s trigger exactly a 65-second sleep and exhaust at exactly 3 retries.
    *   **Contextual 500 Backoff**: Provide specific tests simulating boundary vs. non-boundary LLM failures, ensuring that the chunk shrinking / skipping mechanisms correctly trigger after 5 consecutive failures.
3.  **Filesystem & Path Safety**:
    *   Provide boundary testing on strings $>200$ characters, asserting correct truncation without breaking file extensions.
    *   Pass strings with Windows reserved characters (`<, >, :, ", /, \, |, ?, *`) and Arabic control characters, asserting they are safely sanitized.
    *   Test atomic write functionality: write dummy data to a temp file, ensure the `.tmp` file is created, and successfully confirm the atomic rename to its final destination.
4.  **Logging**:
    *   Write test logs and assert existence in the correctly timestamped `./logs` directory.
    *   Verify the `JSONL` formatting strictly parses as valid JSON on each line and correctly captures the mocked request/response payload of the LLM client.
