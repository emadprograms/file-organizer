---
status: resolved
trigger: "also for each tenant I want to be able to see that he was there for so on to so on. just like the folder does it. there is no way to see that. add that too."
updated: 2026-09-02
---

# Debug Session: tenant-date-range

## Symptoms
- **Expected behavior**: Tenant names in the UI sidebar should display their active date ranges (e.g. `(2015 - 2018)`).
- **Actual behavior**: Tenant names in the UI sidebar are displayed without date ranges, making it hard to see their timeline.
- **Error messages**: None.
- **Timeline**: Always.
- **Reproduction**: Look at the sidebar tree.

## Resolution
- **root_cause**: The `get_tree` API endpoint was extracting only the tenant names and populating `TreeItemResponse.name` with just the name string, dropping the timeline date information stored in the documents.
- **fix**: Updated `get_tree` in `src/api/routes.py` to parse document dates on the fly, calculate the `min` and `max` year for each tenant, and format the `display_name` to append `(YYYY - YYYY)`. The `id` field was intentionally left unmodified so that frontend routing and timeline/category filtering remain perfectly intact.
- **verification**: Tests passed successfully. Verified API returns `"نصار أحمد الأنصاري (2001 - 2025)"`.
- **files_changed**:
  - `src/api/routes.py`
