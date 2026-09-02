---
status: resolved
trigger: "also he houses are are not sorted based on ascending order. 1245 is first and 510 is somewhere at the bttom. fix this too."
updated: 2026-09-02
---

# Debug Session: house-sorting

## Symptoms
- **Expected behavior**: Houses in the sidebar should be sorted numerically (e.g., 510 comes before 1245).
- **Actual behavior**: Houses were sorted alphabetically as strings (where "1245" comes before "510" because '1' < '5').
- **Error messages**: None.
- **Timeline**: Always.
- **Reproduction**: Look at the sidebar tree houses.

## Resolution
- **root_cause**: `os.scandir` / `Path.iterdir()` sorting was using default string lexicographical comparison on directory names.
- **fix**: Introduced `_house_sort_key` in `src/api/routes.py` to extract the numerical house ID using regex and sort based on the integer value. Applied to both `get_tree` and `get_search_index`.
- **verification**: Tests passed and manual verification confirmed the fix.
- **files_changed**:
  - `src/api/routes.py`
