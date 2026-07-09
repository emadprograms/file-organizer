# Phase 09 Validation: Rate Limiting & Router Safety Net

## 1. Validation Strategy
The validation strategy for Phase 09 focuses on **Deterministic Behavior Verification**. Because this phase replaces "graceful" (probabilistic) error handling with "Correctness First" (deterministic) handling, validation relies on simulating specific failure modes using mocks and verifying the system's reaction against strict time and state constraints.

**Key Validation Pillars:**
- **Temporal Verification:** Ensuring wait times are exactly 65s for 429s and 15s for 500s.
- **State Transition Verification:** Ensuring providers are NOT switched on 429s but ARE switched on 500s.
- **Halt Verification:** Ensuring that auth errors (401/403) and retry exhaustion trigger immediate process termination (exceptions) rather than fallback values.
- **Static Analysis:** Using grep to prove the total removal of the "lockout" and "fallback" mechanisms in the router.

## 2. Requirement Mapping

| Req ID | Requirement | Verification Method | Test Case / File |
| :--- | :--- | :--- | :--- |
| **RES-01** | 429 Rate Limit: 65s wait, same provider, 3 retries $ightarrow$ Halt | Mocked API Response $ightarrow$ Time/Provider Check | `tests/test_llm.py` (Case 1) |
| **RES-02** | 500/503 Server Error: 15s wait, switch provider, 3 retries $ightarrow$ Halt | Mocked API Response $ightarrow$ Time/Provider Check | `tests/test_llm.py` (Case 2 & 5) |
| **RES-03** | Correctness First: Remove lockout & fallbacks, Hard Stop | Static Analysis + Functional Halt Test | `src/processing/routing/router.py` |
| **CRIT-01** | Auth Errors (401/403): Immediate Halt | Mocked API Response $ightarrow$ Exception Check | `tests/test_llm.py` (Case 3) |
| **CRIT-02** | Exhaustion: 4 total failed attempts $ightarrow$ Halt | Mocked API Response $ightarrow$ Exception Check | `tests/test_llm.py` (Case 4) |

## 3. Validation Execution

### A. Automated Test Suite
Run the LLM resilience tests to verify the deterministic loop:
```bash
pytest tests/test_llm.py
```

### B. Static Analysis (Safety Net Audit)
Verify that the "graceful" failure logic has been surgically removed from the router:

**Check 1: Removal of Lockout Counter**
```bash
grep -v '^#' src/processing/routing/router.py | grep -c "consecutive_routing_failures" == 0
```

**Check 2: Removal of 13_others Fallbacks**
```bash
grep "return "13_others", False" src/processing/routing/router.py | grep -v "fallback to 13_others" | grep -c "return" == 0
```

### C. Functional Halt Test
Run a routing operation with a mocked LLM that is configured to fail all 4 attempts. Verify that the application raises a `LLMFailureError` and terminates the pipeline rather than assigning the document to a fallback folder.

## 4. Pass Criteria

The phase is considered **PASSED** when:
1. [ ] **Deterministic Resilience:** All tests in `tests/test_llm.py` pass, confirming exact sleep timings and provider switching logic.
2. [ ] **Zero Graceful Fallbacks:** Static analysis confirms `consecutive_routing_failures` and fallback returns to `"13_others"` are completely absent from `src/processing/routing/router.py`.
3. [ ] **Hard Stop Enforcement:** Unrecoverable LLM errors (Auth errors or Retry exhaustion) result in a raised exception that halts the pipeline execution.
