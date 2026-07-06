# Phase 10: Close gaps: sanitize_filename & LLM 500 handling - Summary

## Goal Achievement
**Goal:** Standardize `sanitize_filename` across the project to ensure file extensions are preserved while maintaining safety truncations. Implement a global LLM 500 error counter to abort the pipeline cleanly upon persistent failure.
**Status:** **ACHIEVED**.

## Implementation Details

### 1. Filename Sanitization Standardized
- **Centralized Implementation:** The definitive `sanitize_filename` now lives in `src/core/utils.py`.
- **Extension Preservation:** Updated the truncation logic to use `os.path.splitext`. If a filename exceeds `max_length`, the root is truncated while the extension is preserved, ensuring files remain usable.
- **Cleanup:** Removed the duplicate and legacy implementation from `src/fs_utils.py` to prevent accidental usage of the non-extension-aware version.

### 2. Global LLM Circuit Breaker
- **State Tracking:** Added `global_consecutive_500_errors` to `LLMClient`.
- **Failure Logic:** In `_route_llm_call`, if all available providers fail with a 5xx error or timeout, the global counter increments.
- **Hard Abort:** Upon reaching 5 consecutive global failures, the client raises `LLMFailureError`, triggering an immediate pipeline abort. This prevents the system from spending API quota and time on a service that is fundamentally down.
- **Recovery:** The counter resets to 0 immediately upon any successful response from any provider.

## Verification Results
- **Unit Tests:** Verified `sanitize_filename` behavior in `tests/test_fs_utils.py`.
- **Error Handling:** Verified that persistent 500 errors trigger a halt in `tests/test_llm.py`.
- **Integration:** Confirmed `src/processing/organizer.py` correctly utilizes the centralized utility.
