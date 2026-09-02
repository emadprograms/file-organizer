---
status: resolved
trigger: "also in the app instead of alheen it shows the year. i don't want it to show the year I want it to show present"
updated: 2026-09-02
---

# Debug Session: timeline-present

## Symptoms
- **Expected behavior**: Tenants whose timeline is active up to the current day should display `"Present"` instead of the current year (e.g., `2001 - Present` instead of `2001 - 2026`), mirroring the "الآن" (alheen) convention used in the file system folders.
- **Actual behavior**: The UI was hardcoding the maximum document year (e.g., `2026`) in the subtitle badge.
- **Error messages**: None.
- **Timeline**: Always.
- **Reproduction**: Look at the date badge of an active tenant.

## Resolution
- **root_cause**: The API's `get_tree` endpoint was purely calculating `min()` and `max()` from document dates without checking if the backend YAML parser had designated the tenant as "present".
- **fix**: 
  - Updated `get_tree` in `src/api/routes.py` to cross-reference `state_data.get("routed_documents", {}).get("per_page", [])`.
  - Scanned the original `target_folder` paths for occurrences of the string `"الآن"` or `"present"`.
  - If found, the subtitle is formatted as `{min_val} - Present` instead of `{min_val} - {max_val}`.
- **verification**: Manual verification via API response confirms the subtitle property correctly displays `"2001 - Present"`.
- **files_changed**:
  - `src/api/routes.py`
