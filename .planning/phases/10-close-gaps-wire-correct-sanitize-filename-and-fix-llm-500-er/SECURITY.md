# Security Audit: Phase 10

## Phase Goal
Standardize filename sanitization and implement a global circuit breaker for LLM server errors (5xx) to prevent silent failures and partial, degraded output.

## Threat Model & Mitigations

### 1. Filename Integrity & System Safety
**Threat**: Inconsistent or weak filename sanitization could lead to the creation of invalid files on the filesystem, or in extreme cases, path traversal if input is not properly neutralized.
**Mitigation**: 
- Centralized `sanitize_filename` in `src/core/utils.py`.
- Implements `NFC` normalization to handle Unicode consistency.
- Explicitly replaces illegal characters `[/\:*?"<>|]` with underscores.
- Removes invisible control characters using `unicodedata.category(ch) not in ('Cc', 'Cf')`.
- **Extension Preservation**: Uses `os.path.splitext` during truncation to ensure that the file extension (e.g., `.pdf`) is preserved even when the base name is truncated to fit `max_length`.
**Verification**: 
- Verified in `src/core/utils.py`.
- Duplicate implementation in `src/fs_utils.py` removed.

### 2. Pipeline Resource Exhaustion (LLM 500 Loop)
**Threat**: Persistent LLM server errors (500/503/Timeout) could lead to the pipeline running for extended periods without progress, potentially hitting other rate limits or filling logs with repetitive errors.
**Mitigation**: 
- **Global Circuit Breaker**: `LLMClient` now tracks `global_consecutive_500_errors`.
- If 5 consecutive calls across the entire pipeline fail with 5xx/Timeout, an `LLMFailureError` is raised, aborting the execution.
- The counter is reset upon any successful API call, ensuring temporary glitches don't trigger the breaker.
**Verification**: 
- Verified in `src/llm/llm.py` within `_route_llm_call`.

### 3. Silent Failures & Degraded Output
**Threat**: Generic `except Exception` blocks in the processing layers (`routing.py`, `grouping.py`) might swallow the `LLMFailureError`, causing the system to fall back to "Unassigned" or "13_others" categories. This results in "silent failures" where the user receives a successful exit code but the data is incorrectly organized.
**Mitigation**: 
- **Explicit Exception Bubbling**: Added `except LLMFailureError: raise` blocks immediately preceding generic exception handlers in `src/processing/routing.py` and `src/processing/grouping.py`.
- This ensures that the global circuit breaker's signal reaches the top-level CLI, triggering a non-zero exit and alerting the user.
**Verification**: 
- Verified in `src/processing/routing.py` (`route_document`).
- Verified in `src/processing/grouping.py` (`process_with_shrink`).

## Audit Summary

| Threat | Mitigation | Status | Verification Method |
|---------|------------|--------|----------------------|
| Path/Filename Safety | Centralized extension-aware sanitization | ✅ Verified | Code Review (`src/core/utils.py`) |
| LLM 500 Loop | Global consecutive error counter | ✅ Verified | Code Review (`src/llm/llm.py`) |
| Silent Failures | Explicit `LLMFailureError` bubbling | ✅ Verified | Code Review (`routing.py`, `grouping.py`) |

**Conclusion**: All identified threats for Phase 10 have been mitigated. The system now fails fast and loudly upon persistent server failure, and ensures filesystem safety through standardized sanitization.
