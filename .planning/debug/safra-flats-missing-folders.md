---
status: investigating
trigger: |
  DATA_START
  safra flats isn't working. its not even detecting the folders and files. just the house names.
  DATA_END
---
# Debug Session: Safra Flats missing folders and files

## Symptoms
- **Expected behavior**: The app should detect folders and files for houses under "Safra Flats".
- **Actual behavior**: The app only detects the house names, but no folders or files within them are detected.
- **Error messages**: None specified.
- **Timeline**: N/A
- **Reproduction**: View "Safra Flats" houses in the app, observe that no folders/files are populated.

## Current Focus
- hypothesis: The bug "its showing dot instead of arrows" occurs because `get_tree` fails to extract tenants from the state JSON. The recent change to `_get_document_groups` prioritized `routed_documents` over `grouped_documents` when both lacked `vault_id`. For older pipelines like Safra C and Safra Flats, `routed_documents` was returned (if it was a list) but lacked `primary_tenant`, causing the tree logic to yield 0 tenants, and the UI rendered a dot (`•`) instead of a chevron (`▶`).
- next_action: Fix applied by prioritizing `grouped_documents` in the fallback order within `_get_document_groups`, ensuring backwards compatibility for Safra C/Flats while preserving the Safra D fix. Added a Playwright test `test_safra_c_missing_arrows.py` to prevent regressions.
