---
wave: 4
depends_on:
  - 01-PLAN.md
files_modified:
  - src/processing/routing.py
  - tests/test_routing.py
autonomous: true
---

# Phase 3 - Plan 4: Routing Engine

## Requirements
- GRP-08: Route documents using hardcoded rules
- GRP-09: Single-match categories route directly
- GRP-10: Multi-match categories use LLM

## Tasks

```xml
<task>
  <action>Define Hardcoded Routing Dictionaries</action>
  <read_first>
    - src/processing/routing.py (create if needed)
  </read_first>
  <acceptance_criteria>
    - `FOLDER_ROUTING` maps 13 folders to categories as defined in RESEARCH.md.
    - `CATEGORY_TO_FOLDERS` is dynamically built or hardcoded to reverse-map category to folders.
    - `SINGLE_MATCH` and `MULTI_MATCH` sets are defined correctly.
  </acceptance_criteria>
</task>

<task>
  <action>Implement `route_document` with LLM fallback</action>
  <read_first>
    - src/processing/routing.py
  </read_first>
  <acceptance_criteria>
    - `route_document(group: DocumentGroup, llm_client) -> tuple[str, bool]` returns the folder path and a boolean indicating if it was direct-routed.
    - If `category` is in `SINGLE_MATCH`, returns the folder and `True`.
    - If `category` is in `MULTI_MATCH`, calls LLM to pick the best folder from allowed folders.
    - LLM prompt provides explanations of allowed folders.
    - If LLM fails or picks an invalid folder, retries once. If it fails again, returns "13_others" and `False` (satisfies D-02).
    - Test `test_single_match_direct` and `test_multi_match_llm` pass.
  </acceptance_criteria>
</task>
```

## Verification
- Unit tests verify that single-match documents don't call the LLM and multi-match documents return valid folders or fallback to "13_others".

## Must Haves
- Single-match docs must completely bypass the LLM.
- Must implement D-02 (Multi-match Routing Fallback) by falling back to "13_others" on double failure.

## Artifacts this phase produces
- `FOLDER_ROUTING` (Constant dict)
- `CATEGORY_TO_FOLDERS` (Constant dict)
- `SINGLE_MATCH` (Constant set)
- `MULTI_MATCH` (Constant set)
- `route_document` (Function)
- `tests/test_routing.py` (New File)
