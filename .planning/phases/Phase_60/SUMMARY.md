# Phase 60 Summary

**Goal:** Build a script to ingest old messy `_report.json` files and generate the new chronological format to bring legacy houses up to the v5.5 standard.

## What was done
1. Created `src/migrate.py` which takes a target path.
2. The script processes each valid house directory (identified by `.source_files/` and `_state.json`).
3. For each house, it removes the old `_report.json`.
4. It reads the `.lnk` files in the `[Timeline View]` folder, ordered alphabetically (which represents chronological timeline order).
5. It uses the timeline shortcuts to lookup `vault_id`s in the `routed_documents` loaded from `_state.json`.
6. A new `_report.json` is generated, where documents are explicitly ordered according to the timeline shortcuts, including the `timeline_name`.
7. Wrote comprehensive tests in `tests/test_migrate.py`.

## Next Steps
Proceed to Phase 61: Test Suite Update.