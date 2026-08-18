# Requirements: Milestone v7.0 (The Ingest & Bulletproof Reconcile Engine)

## Objective
Replace the fragile `watcher/prepend` background system with a decoupled, asynchronous pipeline consisting of an explicit `ingest` command and a bulletproof `reconcile` command. This achieves zero-delta idempotency for timeline views, eliminates complex PID locking, and provides a safe pre-reconcile undo mechanism.

## Functional Requirements
1. **Bulletproof Reconcile Upgrade**:
   - `reconcile` must extract metadata (Category and Tenant) from the physical directory structure when a raw PDF is encountered without a manifest.
   - Must ignore PDFs placed in the house root, tenant root, or non-canonical folders.
   - `reconcile` becomes the singular engine for creating vault entries, generating `.lnk` shortcuts, building the `00_Timeline_View`, and updating `state.json`.

2. **The `ingest` Command**:
   - Executes the AI pipeline (Pass 0 to Pass 5: Categorization, Cleaning, Fine Categorization, Grouping, Routing).
   - Bootstraps new houses by generating `.source_files/`, `tenants.yaml`, and an empty `state.json` if they do not exist.
   - Slices and compresses the original PDF into physical PDFs dropped directly into target category folders.
   - Writes an `_ingest_manifest.json` sidecar file containing rich AI metadata.

3. **Manifest Integration**:
   - If `reconcile` finds an `_ingest_manifest.json` matching a raw PDF, it must merge the rich metadata (content explanations, reasoning) directly into `state.json` instead of falling back to basic folder path extraction.

4. **Safe Undo Mechanisms**:
   - `ingest --undo`: Deletes any raw `.pdf` files located in user-facing category folders (ignoring `.source_files/`).
   - `undo`: The system `undo` command must be refactored to move vaulted PDFs to a `.trash/` directory (appending timestamps to prevent collisions) rather than permanently deleting them with `shutil.rmtree`.

5. **Code Deletions**:
   - Delete the background watcher logic (`src/watcher/`, `src/inbox/`).
   - Remove the `prepend` and `create` CLI commands entirely.

## Non-Functional Requirements
- **Test-Driven**: E2E test files (e.g. `tests/m6_ingest_reconcile/`) utilizing `PyMuPDF` (`fitz`) to generate blank physical PDFs on-the-fly must be built and validated *before* any production code is written.
- **Idempotency**: Running `ingest`, followed by `reconcile`, followed by `reconcile` again must result in 0 changes on the second reconcile.
