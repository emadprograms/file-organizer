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
(Empty)

## Fix Plan
(Empty)
