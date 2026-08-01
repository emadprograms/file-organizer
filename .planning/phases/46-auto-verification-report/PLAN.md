# Phase 46: Auto-Verification & Reconciliation Report Plan

## Goal
Automatically run verification after reconciliation, and generate a comprehensive JSON report (along with a console summary) summarizing all actions taken during the reconciliation.

## Strategy
1. **Auto-Verification (REQ-06)**
   - `run_verification` exists in `src/reconcile/verify.py`. It takes args with `target_dir` and checks for orphans, missing shortcuts, and invalid links.
   - At the end of `run_reconcile_mode` in `src/reconcile/core.py`, if it's not a dry run and we succeeded, invoke `run_verification(args)`.
   - Wait, `run_verification` takes an `args` namespace and returns an `int` (0 for pass, 1 for fail).
   - If verification fails, log a warning (it shouldn't necessarily fail the reconciliation since reconciliation already did what it could).

2. **Reconciliation Report (REQ-07)**
   - Create a `report` dictionary at the beginning of `run_reconcile_mode`.
     ```python
     report = {
         "ghost_adopted": 0,
         "raw_pdf_ingested": 0,
         "user_deleted": 0,
         "orphans_trashed": 0,
         "renamed_moved": 0,
         "duplicates_adopted": 0,
         "file_moves_planned": 0,
         "verification_status": "Unknown"
     }
     ```
   - Update counters throughout `run_reconcile_mode` where actions are performed.
   - Save the `report` as `reconcile_report.json` in `.source_files/`.
   - Print a human-readable console summary at the end.

3. **Testing**
   - Write tests in `tests/test_reconcile_phase46.py`.
   - Mock all actions to verify counters increment.
   - Assert `reconcile_report.json` is generated correctly.
   - Assert verification is called.
