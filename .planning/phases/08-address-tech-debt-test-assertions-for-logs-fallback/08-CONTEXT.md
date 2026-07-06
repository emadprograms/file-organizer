# Phase 08: address-tech-debt-test-assertions-for-logs-fallback - Context

**Gathered:** 2026-07-05T21:43:00+03:00
**Status:** ● Complete

## Phase Boundary

Address tech debt related to test assertions for logging logic (like reconciliation output) and fallback behavior (Unassigned folder logic, LLM consecutive errors). This ensures we have robust tests for cross-phase fallbacks and logging outputs.

## Implementation Decisions

### Reconciliation log assertions
- **D-01:** Test reconciliation report output by asserting on both stdout (using capsys) and parsing the `app.log` file to ensure it appears in both console and file.

### "Unassigned" folder fallback tests
- **D-02:** Use both unit tests for logic (in `test_cleaning.py`) and an E2E pipeline mock for integration to test the Unassigned folder fallback behavior.

### LLM consecutive errors mock
- **D-03:** Switch to using `responses` or `pytest-httpx` to mock actual HTTP traffic for LLM consecutive errors (more realistic but might require refactoring of existing LLMClient tests).

### the agent's Discretion
None

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Fallback Logic
- `src/processing/routing.py` — Existing fallback logic for routing
- `src/processing/pipeline.py` — Cross-phase logic and Unassigned fallback
- `src/llm/llm.py` — LLM retry and consecutive error tracking

### Logging
- `src/logger.py` — Logging setup and audit structures
- `tests/test_logger.py` — Current test state for logging

## Existing Code Insights

### Reusable Assets
- `tests/test_routing.py`: Good examples of mocking routing outputs.
- `tests/test_pipeline.py`: Contains E2E mock patterns for pipeline.

### Established Patterns
- We currently use `unittest.mock.patch` for `LLMClient` (see `test_llm.py`, `test_fallback_chain.py`). We will transition to `responses` or `pytest-httpx` for the HTTP mocking.

### Integration Points
- Refactoring `LLMClient` tests might affect `test_fallback_chain.py` and `test_llm.py` heavily.

## Specific Ideas
No specific requirements — open to standard approaches

## Deferred Ideas
None — discussion stayed within phase scope

---

*Phase: 08-address-tech-debt-test-assertions-for-logs-fallback*
*Context gathered: 2026-07-05T21:43:00+03:00*
