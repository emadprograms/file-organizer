# Phase 47: Reconciliation Test Suite Plan

## Goal
Ensure comprehensive test coverage for all reconciliation edge cases (ghost files, user deletions, raw PDF drops, duplicate shortcuts, renames, auto-verification integration). 

## Strategy
1. We have incrementally built `tests/test_reconcile_phase43.py`, `test_reconcile_phase44.py`, `test_reconcile_phase45.py`, and `test_reconcile_phase46.py` throughout the v5.3 milestone.
2. In this phase, we will review the existing tests to ensure they explicitly validate:
   - `state.json` updates (PageData, DocumentGroup, manifest) for each scenario.
   - Filesystem changes (moves to `.trash`, new `vault` files).
   - Expected `reconcile_report.json` outputs.
3. We will add any missing assertions to these files.
4. Finally, run the entire test suite `pytest tests/` to confirm that all tests pass cleanly.
