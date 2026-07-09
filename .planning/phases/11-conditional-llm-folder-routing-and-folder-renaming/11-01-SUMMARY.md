---
phase: 11
plan: 01
subsystem: processing/routing
tags: [routing, direct-routing, arabic-mapping]
dependency-graph:
  requires: [core-schemas]
  provides: [direct-routing-infra]
  affects: [document-pipeline]
tech-stack:
  added: [pydantic-validation]
  patterns: [direct-lookup-fallback]
key-files:
  - src/processing/routing/config.py
  - src/processing/routing/router.py
  - tests/test_routing.py
decisions:
  - "Use a hardcoded mapping in config.py for Arabic folder names to ensure consistency."
  - "Implement a `DIRECT_ROUTED_CATEGORIES` set to explicitly define which categories bypass the LLM for performance and reliability."
metrics:
  duration: "unknown"
  completed-date: "2026-07-09"
status: complete
---

# Phase 11 Plan 01: Folder Mapping and Direct Routing Infrastructure Summary

Implemented the mapping between document categories and their corresponding Arabic folder names, along with a direct routing mechanism to bypass the LLM for high-confidence categories.

## Completed Work

### 1. Arabic Folder Mapping
Defined a comprehensive mapping in `src/processing/routing/config.py` that associates Arabic folder names with their associated document categories (e.g., "عقود" -> `["CONTRACT"]`). This allows the system to resolve the final folder name used for file organization.

### 2. Direct Routing Infrastructure
Updated `src/processing/routing/router.py` to implement a fast-path for routing:
- **Direct Route:** Categories listed in `DIRECT_ROUTED_CATEGORIES` (such as `PERSONAL_DETAILS`, `CONTRACT`, `EWA_LETTERS`, and `INSPECTION_PICTURES`) are routed immediately to their mapped folder.
- **Single Match:** Categories that map to exactly one folder are also routed directly.
- **LLM Fallback:** Only categories with multiple possible folder mappings are sent to the LLM for resolution.

### 3. Verification
Added and passed unit tests in `tests/test_routing.py` to verify:
- Direct routing for specified categories returns correct Arabic names.
- `is_direct_routed=True` is correctly returned for direct paths.
- The LLM is not called during direct routing.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED
- [x] `src/processing/routing/config.py` contains the Arabic mapping.
- [x] `src/processing/routing/router.py` implements direct routing logic.
- [x] `tests/test_routing.py` verifies direct routing and Arabic folder names.
- [x] All tests in `tests/test_routing.py` passed.
