---
status: investigating
trigger: |
  DATA_START
  what the fuck. that is wrong information. safra c houses do have _state.json
  DATA_END
---
# Debug Session: Safra C state.json exists

## Symptoms
- **Expected behavior**: Safra C should work properly since it DOES have `_state.json` files.
- **Actual behavior**: The previous debugger claimed Safra C lacks `_state.json`, which is incorrect. Safra C houses DO have `_state.json`, but the app is still failing to extract their folders/files (showing dots instead of arrows).
- **Error messages**: None specified.
- **Timeline**: Occurred after the fallback logic in `_get_document_groups` was modified for Safra Flats.
- **Reproduction**: Inspect `_get_document_groups` fallback logic in `src/api/routes.py` and test against actual Safra C `state.json` contents. 

## Current Focus
- hypothesis: Safra C has `_state.json`, but `_get_document_groups` is returning data from a key that doesn't have the necessary fields (`primary_tenant`, `folder_path`, or `category`). For example, the recent change made `grouped_documents` the fallback, but Safra C's `grouped_documents` might be missing `folder_path` or `primary_tenant`, whereas its `routed_documents` has them.
- next_action: find a real Safra C `state.json`, look at its structure, and fix `_get_document_groups` so it correctly handles Safra D, Safra Flats, AND Safra C.
