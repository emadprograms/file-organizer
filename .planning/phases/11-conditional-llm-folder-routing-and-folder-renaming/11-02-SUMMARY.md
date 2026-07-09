---
phase: 11
plan: 11-02
subsystem: routing
tags: [llm-constraints, routing-logic, hallucination-reduction]
dependency_graph:
  requires: [11-01]
  provides: [constrained-routing]
  affects: [src/processing/routing/router.py]
tech-stack:
  added: [pydantic-validation-context]
  patterns: [double-check-verification, constrained-prompting]
key-files:
  - src/processing/routing/router.py
decisions:
  - "Used Pydantic `validation_context` to dynamically enforce allowed folder lists per request, ensuring type-level validation without redefining the schema."
  - "Implemented a two-step confirmation process for 'Miscellaneous' routing to minimize over-categorization into 'Others'."
  - "Added an 'Escape Hatch' ('None of the above') to constrained lists to allow LLM to signal misclassification."
metrics:
  duration: "N/A"
  completed_date: "2026-07-08"
status: complete
---

# Phase 11 Plan 11-02: Constrained LLM Routing and "Others" Double-Check Summary

Implemented a constrained routing mechanism for specific document categories and a rigorous double-check flow for miscellaneous documents to reduce LLM hallucinations and improve routing precision.

## Key Changes

### 1. Constrained Prompting Logic
- **Dynamic Filtering:** In `route_document`, the `allowed_folders` list is now filtered based on the document category. `Forms` and `Letters` categories only see their respective relevant folders.
- **Escape Hatch:** Added `"None of the above"` to constrained lists. If the LLM selects this, the document is automatically routed to the `double_check_others` flow.
- **Type-Level Enforcement:** Leveraged Pydantic's `validation_context` to pass the `allowed_folders` list into the `RoutingResponse` validator, ensuring the LLM's output is strictly validated against the current constraint.
- **Retry Loop:** Implemented a 3-attempt retry mechanism that provides explicit feedback to the LLM when a selected folder is rejected for being outside the allowed list.

### 2. "Others" Double-Check Mechanism
- **Two-Step Verification:** Implemented `double_check_others` for `OTHER_LETTERS` or documents hitting the escape hatch:
    - **Step 1:** Re-evaluates the document against all 13 available folders.
    - **Step 2:** If a specific folder (other than "Miscellaneous") is picked, a second "Confirmation" call is made to verify the choice.
- **Hallucination Handling:** Any invalid or unexpected response during the confirmation step automatically defaults the routing to `رسائل متنوعة` (Miscellaneous Letters).
- **Convergence:** The process ensures a final decision is reached, defaulting to "Miscellaneous" if the LLM fails to confirm a specific folder.

### 3. Validation & Logging
- **Schema Validation:** Updated `RoutingResponse` to use a `field_validator` that checks the `selected_folder` against the `allowed_folders` provided in the context.
- **Traceability:** Integrated `log_decision_trace` to record the category, selected folder, and reasoning for every routing decision.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED
- `src/processing/routing/router.py` modified as planned.
- Pydantic validation context implemented.
- Double-check logic implemented and integrated.
- Unit tests in `tests/test_routing.py` verified.
