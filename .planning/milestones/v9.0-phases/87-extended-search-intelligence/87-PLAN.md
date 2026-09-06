# Phase 87 Plan

1. **Update `SearchResultResponse` model**:
   - In `src/api/models.py`, update `type` field documentation/allowed values to include `"document"`.

2. **Implement Fuzzy Matching for Tenants**:
   - In `src/api/routes.py`, import `difflib`.
   - When searching tenants, if `q in t.lower()` doesn't match, use `difflib.get_close_matches(q, [t.lower()], cutoff=0.6)` or calculate string similarity. Or, collect all tenant names and use `difflib.get_close_matches(q, [t.lower() for t in tenants], cutoff=0.6)`.

3. **Implement Full-Text Document Search**:
   - In `src/api/routes.py` inside the search endpoint loop, also check for `report.json`.
   - Read `report.json` if it exists.
   - For each document in `documents`:
     - Check if `q` is in `content` or `brief_arabic_title`.
     - If matched, append a `SearchResultResponse` with `type="document"`.
     - `url` should link to the document, maybe `/#/area/{area_path}/house/{house_dir_name}/vault/{vault_id}` or `.../document/{vault_id}` (based on how frontend handles it, we will use the existing tenant or vault view URL structure. We'll examine frontend code for exact URL, wait, we don't have document view in phase 86. Maybe we just link to `/#/area/.../house/...`?). Let's check `src/web/` to see what routes exist.

4. **Tests**:
   - Add backend pytest covering fuzzy match and document search in `test_api.py`.
   - Update Playwright test `test_search_ux.py` if necessary or create a new test `test_search_intelligence.py`.
