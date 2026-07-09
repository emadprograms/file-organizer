# Phase 07 UAT: Anti-Hallucination Schema Enforcement

## Objective
Verify that the routing engine correctly identifies hallucinations (invalid folder names) and attempts to recover using a feedback-driven retry loop before failing gracefully.

## Test Scenarios

### Scenario 1: Clean Route
- **Description**: LLM returns a valid folder on the first attempt.
- **Mock Input**: `["8_complaints_and_violations"]`
- **Expected Result**: Immediate success, 1 LLM call.
- **Actual Result**: Success. Folder: `8_complaints_and_violations`, Calls: 1.
- **Verdict**: PASS

### Scenario 2: Recoverable Hallucination
- **Description**: LLM returns an invalid folder, then a valid one on the second attempt.
- **Mock Input**: `["invalid_folder_123", "8_complaints_and_violations"]`
- **Expected Result**: 
    - 1st attempt fails validation.
    - Feedback prompt is constructed and sent.
    - 2nd attempt succeeds.
    - Total 2 LLM calls.
- **Actual Result**: Success. Folder: `8_complaints_and_violations`, Calls: 2. Feedback prompt verified.
- **Verdict**: PASS

### Scenario 3: Terminal Hallucination
- **Description**: LLM returns invalid folders for all 3 allowed attempts.
- **Mock Input**: `["bad_1", "bad_2", "bad_3"]`
- **Expected Result**: 
    - 3 failed validation attempts.
    - `RoutingValidationError` is raised after the final attempt.
- **Actual Result**: Caught `RoutingValidationError` after 3 calls.
- **Verdict**: PASS

## Final Verdict: PASS
The anti-hallucination schema enforcement is working as intended. The system correctly validates LLM output against allowed folders, provides corrective feedback on retries, and enforces a strict failure limit.
