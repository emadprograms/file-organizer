---
status: resolved
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

## Findings
- **Root Cause**: The hypothesis regarding `_get_document_groups` was incorrect; the method was returning correctly formatted `grouped_documents` for Safra C. However, in `src/api/routes.py` (specifically inside the `get_tree` endpoint), the code attempted to access `state_data.get("manifest", {}).get("per_page", [])`. 
- Since Safra C's `_state.json` has `"manifest": null`, `state_data.get("manifest", {})` evaluated to `None`. 
- Calling `.get("per_page", [])` on `None` raised an `AttributeError`. 
- This error was silently caught by a broad `try-except Exception: pass` block surrounding the file parsing, which caused the rest of the parsing (including extracting tenant information via `_get_document_groups`) to be entirely skipped. Thus, no children were appended to the house node, and the UI displayed a dot instead of an arrow.

## Resolution
- Modified `src/api/routes.py` and `patch_routes.py` to safely handle a `null` manifest:
  ```python
  manifest = state_data.get("manifest") or {}
  per_page = manifest.get("per_page", [])
  ```
- Tested locally to ensure that `/api/tree` now correctly returns tenant children for Safra C houses.
