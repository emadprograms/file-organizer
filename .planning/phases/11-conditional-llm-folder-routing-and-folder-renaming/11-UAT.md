---
status: "passed"
---
# Phase 11 UAT: Conditional LLM Folder Routing and Folder Renaming

## Objective
Verify that the conditional routing system correctly handles direct routing, constrained prompting, and the "Others" double-check mechanism, and that all folders use Arabic names.

## Test Scenarios

| ID | Scenario | Expected Result | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| UAT-11-1 | Direct Routing: ID/Contract/Utility Bill/Picture | Bypasses LLM, routes to correct Arabic folder. | ✅ PASS | Verified via script `tests/verify_uat_11_1.py`. |
| UAT-11-2 | Constrained Routing: Form | LLM only sees Form-related folders; routes correctly. | ✅ PASS | Verified via script `tests/verify_uat_11_2.py`. |
| UAT-11-3 | Constrained Routing: Letter | LLM only sees Letter-related folders; routes correctly. | ✅ PASS | Verified via script `tests/verify_uat_11_3.py`. |
| UAT-11-4 | Escape Hatch: "None of the above" | LLM selects "None of the above" $ightarrow$ routed to "Others" flow. | ✅ PASS | Verified via script `tests/verify_uat_11_4.py`. |
| UAT-11-5 | Others Flow: Immediate Misc | LLM selects "رسائل متنوعة" $ightarrow$ routes immediately. | ✅ PASS | Verified via script `tests/verify_uat_11_others_flow.py`. |
| UAT-11-6 | Others Flow: Confirmed Match | LLM selects folder $ightarrow$ confirms in 2nd call $ightarrow$ routes. | ✅ PASS | Verified via script `tests/verify_uat_11_others_flow.py`. |
| UAT-11-7 | Others Flow: Confirmation Change | LLM selects folder $ightarrow$ changes mind/fails $ightarrow$ routes to "رسائل متنوعة". | ✅ PASS | Verified via script `tests/verify_uat_11_others_flow.py`. |
| UAT-11-8 | Others Flow: Hallucination Fallback | LLM returns invalid folder during confirmation $ightarrow$ routes to "رسائل متنوعة". | ✅ PASS | Verified via script `tests/verify_uat_11_others_flow.py`. |
| UAT-11-9 | System-Wide Arabic Names | All output folders on disk are in Arabic. | ✅ PASS | Verified via script `tests/verify_uat_11_9.py`. |

## Execution Log
(Detailed results of each test run will be added here)

