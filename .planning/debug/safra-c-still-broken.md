---
status: resolved
trigger: |
  DATA_START
  nope safra c is still not okay.
  DATA_END
---
# Debug Session: Safra C still not working

## Symptoms
- **Expected behavior**: Safra C should show arrows in the UI and allow expanding to see tenant names, and its timeline/PDFs should work.
- **Actual behavior**: Safra C is still not okay (likely still showing dots instead of arrows, or missing PDFs, despite the recent fix that was supposed to address Safra Flats and older pipelines).
- **Error messages**: None specified.
- **Timeline**: Occurring after the fix for Safra Flats (`safra-flats-missing-folders.md`).
- **Reproduction**: View "Safra C" in the app.

## Evidence
- timestamp: 2026-09-02T17:34:00+03:00 - Investigated Safra C directory in `tests/fixtures/e2e/golden_state/areas/Safra C`.
- timestamp: 2026-09-02T17:34:21+03:00 - Discovered that Safra C houses completely lack a `_state.json` or `_report.json` file in `.source_files`. The only file present is `{house_id}_tenants.yaml`.
- timestamp: 2026-09-02T17:35:10+03:00 - Reviewed previous bug (`safra-flats-missing-folders.md`) and the test `test_safra_c_missing_arrows.py` added for it. The test mocked a `_state.json` file, which is why the previous fix appeared to work, but it did not address the true state of older pipelines on disk, which have no `_state.json` at all.
- timestamp: 2026-09-02T17:36:00+03:00 - The backend API (`get_tree`, `list_timeline`, `list_categories`, `get_search_index`) previously returned 404 or empty results if `_state.json` was missing.

## Current Focus
- hypothesis: Safra C is completely missing `_state.json` files and relies entirely on folder structure and legacy `_tenants.yaml`. The backend tree, timeline, search, and category APIs fail or return empty when `_state.json` is missing.
- next_action: Implement filesystem scanning fallback in `src/api/routes.py` for older pipelines that don't have `_state.json`.

## Resolution
- root_cause: The backend API endpoints strictly required `_state.json` to extract tenant structure, timelines, categories, and PDFs. Older pipelines (like Safra C) only have physical directories (`tenant_name (dates)` -> `category` -> `pdfs`) and lack `_state.json`. The previous fix assumed `_state.json` existed but missed `vault_id`, which was incorrect for Safra C.
- fix: Updated `src/api/routes.py` endpoints (`get_tree`, `list_timeline`, `list_categories`, `get_search_index`, and `get_pdf`) to fallback to scanning the physical directory structure if `_state.json` is absent. Tenant names and dates are parsed from folder names (`Tenant Name (YYYY - YYYY)`), and PDF access is provided using URL-safe base64 encoding of the relative path (`fs_{encoded}`).
