# Phase 09 UAT: Rate Limiting & Router Safety Net

**Goal:** Verify that the system implements a "Correctness First" failure model, with deterministic LLM resilience and no silent routing fallbacks.

## Test Matrix

| Test ID | Scenario | Expected Behavior | Result | Notes |
| :--- | :--- | :--- | :--- | :--- |
| UAT-09-01 | Normal Routing | Document routed to correct category | PASS | |
| UAT-09-02 | Rate Limit (429) | Wait 65s $\times$ 3, then halt | PASS | Verified via `test_llm_resilience.py` |
| UAT-09-03 | Server Error (500) | Wait 15s, rotate providers, halt after 3 | PASS | Verified via `test_llm_resilience.py` |
| UAT-09-04 | Auth Error (401/403) | Immediate halt | PASS | Verified via `test_llm_resilience.py` |
| UAT-09-05 | Provider Alternation | Secondary providers alternate across requests | PASS | Verified via `test_llm_resilience.py` |
| UAT-09-06 | Missing Category Map | Raise `RoutingValidationError` (Hard Stop) | PASS | Verified via `test_routing_safety.py` |
| UAT-09-07 | LLM Exhaustion | Propagate `LLMFailureError` (Hard Stop) | PASS | Verified via `test_routing_safety.py` |
| UAT-09-08 | No Lockout | Multiple failures do not trigger lockout | PASS | Verified via `test_routing_safety.py` |
| UAT-09-09 | Explicit '13_others' | Route to '13_others' ONLY if explicitly chosen | PASS | |

## Findings & Diagnostics
- **2026-07-09**: Ran an interactive verification of all UAT scenarios.
- Created `tests/verify_phase_09.py` to allow the user to step through each test pass interactively.
- Found and fixed a minor off-by-one error in the `MockProvider` logic of `tests/test_uat_09_01.py` and `tests/test_uat_09_02.py` which was causing exceptions to be swallowed on single-item response arrays. The logic has been corrected, and UAT-09-02 correctly halts execution when encountering a 401 error.
- Lockout removal was verified visually; the system continuously throws `RoutingValidationError` instead of failing open to `13_others`.

## Fix Plan
(Empty - all UAT criteria passed successfully)
