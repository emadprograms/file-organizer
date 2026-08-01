# Requirements: v5.3 Reconciliation Engine Upgrade

## 1. Ghost File Adoption (REQ-01)
- The reconciler MUST detect physical shortcuts (`.lnk`) or raw PDFs that exist on disk but have NO corresponding entry in `state.json`.
- For each ghost file, the reconciler MUST create a new `per_page` entry in `state.json` with at minimum: `vault_id`, `output_file`, and any date extractable from the filename.
- After reconciliation, there MUST be zero files on disk unaccounted for in `state.json`.

## 2. User Deletion Detection (REQ-02)
- The reconciler MUST detect when a user has deleted a shortcut from a categorized folder.
- When a shortcut is deleted, the reconciler MUST remove its entry from `state.json`.
- The corresponding vault PDF MUST be moved to a `.source_files/.trash/` folder (not permanently deleted) to allow recovery.
- Orphan vault PDFs (referenced in state but with no shortcut on disk) MUST be cleaned up.

## 3. Raw PDF Ingestion (REQ-03)
- The reconciler MUST detect raw `.pdf` files dropped directly into categorized folders by the user.
- Each raw PDF MUST be automatically moved into `.source_files/vault/` with a new UUID.
- A `.lnk` shortcut MUST be placed in the original location replacing the raw PDF.
- A new `per_page` entry MUST be created in `state.json` for the adopted PDF.

## 4. Duplicate Shortcut Handling (REQ-04)
- The reconciler MUST detect when multiple shortcuts in different folders point to the same vault PDF.
- The `state.json` schema MUST support a single vault PDF appearing in multiple categories (1-to-many).
- Duplicate shortcuts MUST NOT cause reconciliation errors or infinite loops.

## 5. Renamed Shortcut Detection (REQ-05)
- The reconciler MUST detect when a user renames a shortcut file (e.g., `2010-04-01.lnk` → `2010 - Electricity Bill.lnk`).
- The `output_file` field in `state.json` MUST be updated to reflect the new name.
- The renamed shortcut MUST be flagged as `user_locked: true` to prevent the system from reverting the rename.

## 6. Auto-Verification After Reconciliation (REQ-06)
- After every reconciliation run, the system MUST automatically invoke `run_verification()` on the target house.
- If verification fails, the reconciliation MUST report the failures but NOT roll back changes (since the reconciliation may have partially fixed the house).
- The combined reconciliation + verification result MUST be surfaced to the caller.

## 7. Reconciliation Report (REQ-07)
- Every reconciliation run MUST produce a structured report summarizing all actions taken.
- The report MUST include: files adopted, files deleted/trashed, files moved, shortcuts renamed, verification pass/fail status, and error count.
- The report MUST be saved to `.source_files/{house_id}_reconciliation_report.json`.
- The report MUST also be printed to the console in a human-readable summary format.

## 8. Test Coverage (REQ-08)
- MUST include `pytest` tests covering each edge case: ghost files, deletions, raw PDF drops, duplicates, renames.
- Tests MUST validate that `state.json` is correctly updated after each reconciliation scenario.
- Tests MUST validate that auto-verification runs and produces correct pass/fail results.
