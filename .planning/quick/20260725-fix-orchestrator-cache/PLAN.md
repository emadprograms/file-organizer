# Quick Plan: Fix Orchestrator Cache Wipe Bug

## Objective
Fix the orchestrator cache wipe bug to allow resuming from failures.

## Steps
1. Edit `src/watcher/orchestrator.py`:
   - Inside the `propose` method, right after `master_tmp_dir.mkdir(exist_ok=True)`, add `success = False`.
   - Remove ALL occurrences of `shutil.rmtree(master_tmp_dir, ignore_errors=True)` that exist in error paths (except blocks, early returns).
   - At the very end of the final `try` block, add `success = True`.
   - In the final `finally:` block, wrap the `rmtree` call so it only runs on success.
2. Check syntax by running `python -m py_compile src/watcher/orchestrator.py`.
3. Commit changes atomically.
4. Push changes to GitHub.
5. Update `STATE.md` "Quick Tasks Completed" table.
6. Produce `SUMMARY.md`.
