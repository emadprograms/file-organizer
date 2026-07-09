# Phase 09-02 Summary: Router Safety Net Implementation

## Objective
Eliminate all "graceful" fallbacks in the document router to ensure that any routing ambiguity or failure results in a pipeline halt rather than a silent mis-classification into '13_others'. This enforces the "Correctness First" mandate.

## Changes

### Core Logic (`src/processing/routing/router.py`)
- **Removed Lockout Mechanism**: Deleted the `consecutive_routing_failures` counter and the associated logic that would skip routing after multiple failures.
- **Removed Mapping Fallback**: In the `if not allowed_folders:` block, replaced the return of `'13_others'` with a `RoutingValidationError`.
- **Removed Final Fallback**: Eliminated the implicit fallback to `'13_others'` at the end of `route_document`. The function now only exits via a successful route or an exception raised within the LLM retry loop.
- **Exception Wrapping**: Ensured that unexpected exceptions during LLM calls are wrapped in `RoutingValidationError` on the final attempt to provide a consistent failure signal to the pipeline.

### Verification (`tests/test_routing_safety.py`)
- **Corrected Test Categories**: Updated test cases to use categories that are not in `SINGLE_MATCH` (e.g., using `'forms'` instead of `'contract'`). This ensures the tests actually exercise the LLM routing and retry logic rather than hitting the shortcut path.
- **Aligned Exception Expectations**: Updated `test_llm_exhaustion_raises_error` to expect `RoutingValidationError` instead of `RuntimeError`, reflecting the router's wrapping behavior on final attempts.
- **Verified Hard Halts**: Confirmed that unmapped categories, LLM exhaustion, and repeated validation failures all trigger a `RoutingValidationError`.

## Outcome
The routing system is now "fail-fast". No document is routed to `13_others` unless the LLM explicitly selects it as the best fit from the allowed list. This prevents silent data corruption in the organization process.

## Validation Results
- `pytest tests/test_routing_safety.py`: **PASSED** (4/4 tests)
