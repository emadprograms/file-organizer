# Requirements: v5.4 Architectural Consistency Refactor

## 1. 1-to-Many Shortcut Mapping (REQ-01)
- The core data model MUST decouple the concept of "Pages" from "Shortcuts".
- A physical multi-page PDF inside the vault MUST always be represented by its exact physical page count in `state.json` (inside `cleaned_pages` and `per_page` arrays).
- Duplicating shortcuts on the file system MUST NOT inflate the total page count metadata in the database.
- The system MUST gracefully map multiple physical shortcuts to a single grouped document without spawning "virtual pages".

## 2. Cross-House Contamination Immunity (REQ-02)
- The reconciliation engine MUST detect when a shortcut belonging to "House A" is accidentally moved/copied into the categorized folders of "House B".
- The engine MUST NOT crash when attempting to resolve a `vault_id` that belongs to a different house's vault.
- The system MUST quarantine, reject, or safely re-home the contaminated shortcut without breaking the target house's timeline or verification.

## 3. Multi-Page Raw PDF Ingestion (REQ-03)
- When a raw, unmanaged `.pdf` file is manually dropped into a categorized folder by a user, the ingestion engine MUST accurately read the physical page count of the PDF.
- The system MUST record the correct number of pages in `state.json` rather than defaulting to a 1-page assumption.
- The verification engine MUST correctly audit the full page count of newly dropped documents.

## 4. Corrupted Vault File Safeguards (REQ-04)
- The system MUST survive encountering a corrupted, empty, or 0-byte PDF inside the vault.
- Verification and Timeline View generation MUST NOT crash when attempting to parse or link to a corrupted vault document.
- The reconciler MUST flag corrupted vault files during its health-check routines.
