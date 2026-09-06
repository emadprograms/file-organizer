# Phase 85 Plan

1. **Backend `/api/search` Endpoint**
   - Add a `q` parameter to `/api/search`.
   - Iterate through all houses in `areas_root`.
   - Read `.source_files/*_state.json`.
   - Match `q` (case-insensitive) against:
     - House ID / House Name
     - Tenant Names
   - Return a list of matching results.

2. **Frontend UI**
   - Add a `<nav id="top-navbar">` with a `<input id="search-input" type="search" placeholder="Search..." />`.
   - Add a `<div id="search-results"></div>` to display results.
   - Listen for `keydown` on `#search-input`:
     - If `Enter`, fetch `/api/search?q=...` and populate `#search-results`.
     - If `Escape`, clear input and hide `#search-results`.
   - If search results are empty, display "No results" inside `#search-results`.

3. **Tests**
   - Run `pytest` and fix any backend test issues.
   - Run Playwright tests and fix frontend test issues.

4. **Completion**
   - Generate `85-VERIFICATION.md` with `status: passed`.
   - Generate `85-01-SUMMARY.md`.
