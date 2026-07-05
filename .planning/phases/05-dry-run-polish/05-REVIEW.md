---
status: issues_found
files_reviewed: 10
critical: 1
warning: 1
info: 1
total: 3
---

# Code Review - Phase 05: Dry Run Polish

### CR-1: Visualizer Path Parsing Bug
**File:** `src/processing/visualizer.py` (Line 33)
**Severity:** Critical
**Description:** In `Visualizer.print_summary()`, the tree structure is built by parsing the `output_file` paths:
```python
path_parts = p["output_file"].replace("\\", "/").split("/")
if len(path_parts) == 3:
    tenant, category, filename = path_parts
```
However, the `output_file` path (generated in `organizer.py`) is relative to `output_base_dir`, which means it includes the `house_id` as the first component (e.g., `1273/Ahmed/5_contract/nodate.pdf`). Thus, `len(path_parts)` is **4**, not 3. The `if len(path_parts) == 3:` condition will silently fail for all files, resulting in an empty tree output during a dry run.
**Recommendation:** Update the unpacking logic to handle 4 parts:
```python
if len(path_parts) == 4:
    house_id, tenant, category, filename = path_parts
```

### WR-1: Weak Assertions in E2E Test
**File:** `tests/test_e2e.py` (Lines 118-124)
**Severity:** Warning
**Description:** The test `test_dry_run_end_to_end` uses an overly permissive assertion for checking the dry run output:
```python
assert any(
    indicator in combined_output
    for indicator in ["1273", "Ahmed", "contract", "Dry Run", "dry run", "DRY RUN"]
)
```
Because the string "Dry Run" is unconditionally printed in the header (`=== Dry Run Output Preview ===`), the `any()` condition will always be true, even if the tree rendering fails completely (as it does due to `CR-1`).
**Recommendation:** Use `all()` instead of `any()`, or explicitly assert that the tenant (`Ahmed`) and the category (`contract`) are present in the console output to ensure the tree actually renders.

### IN-1: Path Resolution Security
**File:** `src/processing/organizer.py` (Line 97)
**Severity:** Info
**Description:** The check `if not str(target_dir).startswith(str(output_base_dir.resolve())):` is an excellent security measure to prevent path traversal attacks during file extraction. Good implementation.
