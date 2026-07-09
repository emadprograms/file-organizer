# Phase 09: Rate Limiting & Router Safety Net - Summary

## Objective
Implement a deterministic LLM resilience loop that replaces exponential backoff with strict, requirement-driven wait times and provider rotation, ensuring a "Correctness First" failure model.

## Implementation Details

### 1. Exception Hierarchy
- Created `PipelineHaltError` in `src/core/exceptions.py` as a base for critical, unrecoverable errors.
- Updated `LLMFailureError` (in `src/llm/llm.py`) and `RoutingValidationError` (in `src/processing/routing/router.py`) to inherit from `PipelineHaltError`.
- This allows the pipeline orchestrator to catch any "Hard Stop" error with a single base class.

### 2. Deterministic Resilience Loop
Refactored `LLMClient._route_llm_call` in `src/llm/llm.py`:
- **Removed Tenacity**: Replaced exponential backoff with a manual retry loop for total control over timing and rotation.
- **Provider Sequence**: Implemented a deterministic rotation sequence: `[Gemini, S1, S2, Gemini, S3]` (where S1/S2 alternate per request via `_fallback_toggle`).
- **Strict Wait Times**:
    - **429 (Rate Limit)**: Triggers exactly 65s sleep and retries the *same* provider.
    - **500/503 (Server Error/Timeout)**: Triggers 15s sleep and *rotates* to the next provider in the sequence.
- **Fail-Fast Model**: 400, 401, and 403 errors now trigger an immediate `LLMFailureError`, halting the pipeline to prevent wasted credits or silent failures.
- **Dead Code Removal**: Removed legacy `global_consecutive_500_errors` tracking.

### 3. Verification
- Created a TDD suite in `tests/test_llm_resilience.py` using mocked providers and `time.sleep` to verify:
    - 429s wait 65s for exactly 3 retries before failing.
    - 500s wait 15s and rotate providers.
    - 401s halt immediately.
    - Secondary providers alternate deterministically across sequential requests.
- All tests passed.

## Success Criteria Verification
- [x] 429s wait 65s (Verified via `test_resilience_429_retry_limit`)
- [x] 500s wait 15s and rotate (Verified via `test_resilience_500_rotation`)
- [x] 401s halt immediately (Verified via `test_resilience_401_immediate_halt`)
- [x] Rotation alternates providers per request (Verified via `test_provider_alternation`)
- [x] Legacy 500 counter removed (Verified via code review)
- [x] `LLMFailureError` inherits from `PipelineHaltError` (Verified via `issubclass` check)
