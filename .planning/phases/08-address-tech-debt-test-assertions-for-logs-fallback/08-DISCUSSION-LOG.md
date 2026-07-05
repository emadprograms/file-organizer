# Phase 08: address-tech-debt-test-assertions-for-logs-fallback - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-05
**Phase:** 08-address-tech-debt-test-assertions-for-logs-fallback
**Areas discussed:** Reconciliation log assertions, Unassigned folder fallback tests, LLM consecutive errors mock

---

## Reconciliation log assertions

| Option | Description | Selected |
|--------|-------------|----------|
| Parse `app.log` file directly (more robust, tests actual persistent logs) | Parse `app.log` file directly (more robust, tests actual persistent logs) | |
| Assert on stdout using `capsys` (simpler, tests CLI output) | Assert on stdout using `capsys` (simpler, tests CLI output) | |
| Both (ensure it appears in both console and file) | Both (ensure it appears in both console and file) | ✓ |

**User's choice:** Both (ensure it appears in both console and file)
**Notes:** N/A

---

## Unassigned folder fallback tests

| Option | Description | Selected |
|--------|-------------|----------|
| Isolated unit tests in `test_cleaning.py` (simpler, faster) | Isolated unit tests in `test_cleaning.py` (simpler, faster) | |
| Full E2E pipeline test with a mocked unresolvable page | Full E2E pipeline test with a mocked unresolvable page | |
| Both unit tests for logic and an E2E pipeline mock for integration | Both unit tests for logic and an E2E pipeline mock for integration | ✓ |

**User's choice:** Both unit tests for logic and an E2E pipeline mock for integration
**Notes:** N/A

---

## LLM consecutive errors mock

| Option | Description | Selected |
|--------|-------------|----------|
| Continue using `unittest.mock.patch` on `LLMClient` or `GeminiProvider` (consistent with existing tests) | Continue using `unittest.mock.patch` on `LLMClient` or `GeminiProvider` (consistent with existing tests) | |
| Switch to using `responses` or `pytest-httpx` to mock actual HTTP traffic (more realistic but might require refactoring) | Switch to using `responses` or `pytest-httpx` to mock actual HTTP traffic (more realistic but might require refactoring) | ✓ |

**User's choice:** Switch to using `responses` or `pytest-httpx` to mock actual HTTP traffic (more realistic but might require refactoring)
**Notes:** N/A

---

## the agent's Discretion
None

## Deferred Ideas
None
