# Phase 24 Code Review

## Scope
Reviewed files:
- `src/fs_ui/__init__.py`
- `src/fs_ui/lock.py`
- `src/fs_ui/orchestrator.py`
- `src/main.py`
- `tests/test_fs_ui_lock.py`
- `tests/test_fs_ui_orchestrator.py`
- `tests/test_main_file_placement.py`
- `src/reconcile/core.py`

## Findings

### High Severity (Bugs & Vulnerabilities)
1. **Filename String Replacement Bug** (`src/fs_ui/orchestrator.py:220`)
   - **Issue:** `clean_name = filepath.name.replace(" OK.pdf", "").replace("_Proposed", "")` replaces all occurrences of the strings in the filename, not just the suffix. If a tenant or area happens to contain "_Proposed", it will be incorrectly stripped, breaking the area/house resolution.
   - **Recommendation:** Use `.removesuffix(" OK.pdf")` and `.removesuffix("_Proposed")` (if the file could end in `_Proposed OK.pdf`). Or a regex specifically targeting the end of the string.

### Medium Severity (Concurrency & Architecture)
2. **PID Lock Race Condition** (`src/fs_ui/lock.py`)
   - **Issue:** The PID-based locking mechanism has a race condition (TOCTOU). If two instances start simultaneously, check the lockfile, find the previous PID dead, they will both overwrite the lockfile and assume they hold the lock.
   - **Recommendation:** Use OS-level atomic locks like `fcntl.flock()` (on Unix) or a dedicated library like `filelock`.

3. **Unhandled Exceptions in Orchestrator Loop** (`src/fs_ui/orchestrator.py:71-117`)
   - **Issue:** `propose()` is called within the `process_inbox()` `while True:` loop. If an unhandled exception occurs in `propose()` (or `finalize()`), the entire orchestrator process will crash, stopping the background listener.
   - **Recommendation:** Wrap the body of the `for pdf_path in inbox_dir.glob("*.pdf"):` loop in a broad `try...except Exception` to log errors and ensure the listener continues running.

### Low Severity (Code Quality & Smells)
4. **Inline Imports** (`src/fs_ui/orchestrator.py` and `src/main.py`)
   - **Issue:** There are multiple inline imports (e.g., `import fitz`, `import yaml`, `from src.main import run_grouping_pass`) scattered within functions like `finalize()` and `run_append_mode()`.
   - **Recommendation:** Move imports to the top of the file unless specifically required to prevent circular dependencies or to significantly reduce startup time.

5. **Temp Directory Cleanup** (`src/fs_ui/orchestrator.py:38`)
   - **Issue:** `shutil.rmtree(tmp_dir)` is used without `ignore_errors=True` in the stale directory cleanup loop. If a file inside the temp directory is held open, it could raise an exception and prevent other stale directories from being cleaned.
   - **Recommendation:** Add `ignore_errors=True` as is done elsewhere: `shutil.rmtree(tmp_dir, ignore_errors=True)`.
