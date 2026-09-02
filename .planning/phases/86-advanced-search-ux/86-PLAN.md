# Phase 86 Plan: Advanced Search UX

## 1. Modify `src/api/static/index.html`
- Add a global `keydown` event listener to catch `Cmd+K` or `Ctrl+K`. It will call `e.preventDefault()` and `searchInput.focus()`.
- Add an `input` event listener on `search-input` for zero-click search. It will debounce the search input by ~250ms and fetch results from `/api/search` automatically.
- Ensure clicking on a result handles navigation immediately (`a.href = item.url` should work with the existing `#` hash-based router).
- Keep `Escape` key handling to clear and close the search results.

## 2. Update Playwright Tests
- Create or update `tests/frontend/test_advanced_search.py` (or `test_ui.py`).
- Add tests to verify that `Cmd+K` / `Ctrl+K` focuses the search bar.
- Add tests to verify that typing into the search bar instantly shows results (zero-click search) without pressing Enter.
- Add tests to verify clicking a result navigates successfully.

## 3. Verify
- Run `pytest tests/frontend/ -v`.
- Fix any issues until tests pass.
- Generate `86-VERIFICATION.md` with `status: passed`.
- Generate `86-01-SUMMARY.md`.
