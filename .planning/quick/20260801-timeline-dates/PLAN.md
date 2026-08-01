---
description: Update Timeline View shortcut naming convention to include dates and titles across migration and reconciliation.
---

# Plan

1. Update `src/migration/v5_migration.py` to name timeline shortcuts as `{idx:03d} - {date_str} - {title}.lnk` instead of `{idx:03d}_{title}.lnk`.
2. Update `src/reconcile/core.py` to use the same naming convention AND fix the deduplication bug (where multi-page documents generate multiple identical timeline shortcuts).
3. Update `tests/test_migration.py` and `tests/test_reconcile_bidirectional.py` to assert the new timeline link names.
4. Run `pytest` to ensure tests pass.
5. Record `SUMMARY.md`.
