# Phase 60 Plan

## Goal
Build a script `src/migrate.py` to scan existing processed houses, delete the old `_report.json`, read `routed_documents` and Timeline shortcuts, and reconstruct a new timeline-ordered `_report.json`.

## Steps
1. Create `src/migrate.py`.
2. Implement CLI using argparse.
3. For each house directory found:
   a. Check if `.source_files/<house_id>_state.json` exists.
   b. Load `State`.
   c. Read `[Timeline View]` shortcuts and resolve their targets to find `vault_id`.
   d. Order `routed_documents` based on the chronological order of the Timeline shortcuts.
   e. Delete old `_report.json`.
   f. Generate and save the new `_report.json`.
4. Write tests in `tests/test_migrate.py`.
5. Update `ROADMAP.md` and `STATE.md`.