# Requirements: v5.4 Architectural Consistency Refactor

## 1. 1-to-Many Shortcut Mapping (REQ-01) (Phase 49)
- The core data model MUST decouple the concept of "Pages" from "Shortcuts".
- A physical multi-page PDF inside the vault MUST always be represented by its exact physical page count in `state.json` (inside `cleaned_pages` and `per_page` arrays).
- Duplicating shortcuts on the file system MUST NOT inflate the total page count metadata in the database.
- The system MUST gracefully map multiple physical shortcuts to a single grouped document without spawning "virtual pages".

## 2. Cross-House Contamination Immunity (REQ-02) (Phase 50)
- The reconciliation engine MUST detect when a shortcut belonging to "House A" is accidentally moved/copied into the categorized folders of "House B".
- The engine MUST NOT crash when attempting to resolve a `vault_id` that belongs to a different house's vault.
- The system MUST quarantine, reject, or safely re-home the contaminated shortcut without breaking the target house's timeline or verification.

## 3. Multi-Page Raw PDF Ingestion (REQ-03) (Phase 51)
- When a raw, unmanaged `.pdf` file is manually dropped into a categorized folder by a user, the ingestion engine MUST accurately read the physical page count of the PDF.
- The system MUST record the correct number of pages in `state.json` rather than defaulting to a 1-page assumption.
- The verification engine MUST correctly audit the full page count of newly dropped documents.

## 4. Corrupted Vault File Safeguards (REQ-04) (Phase 52)
- The system MUST survive encountering a corrupted, empty, or 0-byte PDF inside the vault.
- Verification and Timeline View generation MUST NOT crash when attempting to parse or link to a corrupted vault document.
- The reconciler MUST flag corrupted vault files during its health-check routines.

## 5. Nested Folder Trap (REQ-05) (Phase 53)
- The system MUST gracefully handle cases where a user creates manual sub-directories inside a categorized folder (e.g., `05_عقود/Old Versions/contract.lnk`).
- The reconciler MUST NOT crash or confuse downstream LLMs when extracting `target_folder` paths that contain unexpected deep nesting.
- The verification engine MUST correctly validate shortcuts placed in arbitrary sub-folders within the tenant's root folder.

## 6. Tenant Root Folder Renaming (REQ-06) (Phase 54)
- The system MUST survive the scenario where a user renames the top-level tenant folder (e.g., from `أحمد قايد صالح سيف ‎(2002 - الآن)‎` to `أحمد قايد (2002)`).
- The reconciler MUST NOT aggressively auto-revert the user's rename or trap itself in an endless loop fighting the user's manual change.
- `state.json` MUST accurately reflect the new folder paths without breaking the canonical tenant linkage to `tenants.yaml`.

## 7. Shortcut Target Hijack / Corruption (REQ-07) (Phase 55)
- The reconciler MUST detect if a valid `.lnk` file is modified to point outside the Vault (e.g., pointing to `C:\Downloads\file.pdf` instead of `.source_files\vault\...`).
- The system MUST NOT treat a target-hijacked shortcut as a "user deletion" of the original Vault PDF, preventing accidental data loss or vault cleanup.
- The verification script MUST flag hijacked or broken shortcuts explicitly so the user is warned.

## 8. Idempotency Guarantee (REQ-08) (Phase 56)
- The reconciliation process MUST be safely repeatable. Running the engine multiple times back-to-back without manual filesystem changes MUST result in zero side-effects.
- Ghost adoption and raw PDF ingestion MUST NOT double-count or re-process files on subsequent runs.
- `state.json` metadata (like page counts and indices) MUST remain stable across redundant runs.

## 9. File Locking Resilience (REQ-09) (Phase 57)
- The system MUST gracefully handle scenarios where the user has a PDF file currently open in a viewer (e.g., Adobe Acrobat, Chrome).
- If `shutil.move()` or similar file operations raise a `PermissionError` due to file locks, the reconciler MUST catch the error and skip the operation instead of crashing.
- File lock failures MUST NOT result in a partially written `state.json` that corrupts the internal tracking; state updates must be atomic or safe from partial application.
