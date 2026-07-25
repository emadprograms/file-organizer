---
status: complete
---

# 20260725-fix-orchestrator-cache

## Objective
Fix the orchestrator cache wipe bug to allow resuming from failures.

## Actions Taken
1. Added `success = False` flag at the start of the `propose` method in `src/watcher/orchestrator.py` after creating `master_tmp_dir`.
2. Removed all `shutil.rmtree(master_tmp_dir, ignore_errors=True)` statements from intermediate error paths to preserve the cache.
3. Added `success = True` at the end of the final try block when processing succeeds.
4. Updated the `finally:` block to only remove the directory `if success:`.
5. Checked syntax with `py_compile`.
6. Committed with message "fix: preserve orchestrator tmp cache on failure to allow resuming" and pushed.
7. Logged the task as pending/complete in `STATE.md`.
