# Research: Vault Architecture & Bidirectional Reconciliation Features

This document outlines the architectural patterns and expected behaviors for the features targeted in the v5.0 milestone of the document management system. 

## 1. Vault / Content-Addressed Storage (CAS)
**Concept:**
Modern systems (like Git, Time Machine, or Digital Asset Management systems) separate *storage* from *presentation*. Originals are ingested into a hidden, immutable "Vault," often organized by unique IDs or cryptographic hashes (Content-Addressed Storage), rather than human-readable folder trees.
- **Table Stakes:** Storing originals safely in a single directory; immutability (files are never modified or renamed once ingested); robust unique ID generation (e.g., UUIDs or SHA256).
- **Differentiators:** Content-addressing for automatic deduplication of identical PDFs; file integrity verification.
- **Anti-features:** Using the Vault directory for human browsing; modifying Vault files directly; relying on nested folder structures inside the Vault.
- **Complexity:** Medium. Requires robust ID generation, preventing race conditions during ingestion, and careful handling of file locks on Windows.
- **Dependencies:** Feeds from the existing **PDF extraction** and **multi-page grouping**. The vault acts as the final destination for the physical file.

## 2. Shortcut / Symlink-Based Organization
**Concept:**
Systems project "views" onto the immutable storage using pointers. Because the target OS is Windows, `.lnk` shortcuts are used instead of POSIX symlinks or hardlinks. This allows a single document to appear in multiple logical locations (e.g., a timeline view and a category folder) without duplicating disk usage.
- **Table Stakes:** Generating valid `.lnk` files that seamlessly open the Vault target; resolving relative/absolute paths correctly so shortcuts survive folder moves on the same drive.
- **Differentiators:** Multi-axis categorization (putting the same document in multiple folders simultaneously based on metadata).
- **Anti-features:** Creating brittle shortcuts that break if the parent application folder is moved; using macOS symlinks or hardlinks on Windows.
- **Complexity:** Low to Medium. Requires utilizing Windows-specific APIs (via `pywin32`, `winshell`, or VBScript wrappers) to generate `.lnk` files programmatically.
- **Dependencies:** Relies directly on the **Vault (VAULT)** for target paths. Replaces the existing physical file movement currently handled by the **Routing to Arabic folders** logic.

## 3. Bidirectional Sync & Reconciliation Engines
**Concept:**
Systems like Dropbox, OneDrive, and Syncthing maintain a source of truth (local state file or remote server) and compare it against the physical file system. By diffing the expected state against the actual state, the system can detect if a user deleted, renamed, or moved a file.
- **Table Stakes:** Detecting missing shortcuts (user deleted it); detecting moved shortcuts (user re-categorized it); updating a central state file to match reality.
- **Differentiators:** Gracefully handling offline/external modifications; detecting when a user copies a shortcut vs moves it.
- **Anti-features:** One-way syncs that silently overwrite manual user corrections; infinite reconciliation loops where the system and user constantly fight over file placement.
- **Complexity:** High. Requires a rock-solid diffing algorithm between the new **Unified `state.json`** and the filesystem tree, while avoiding false positives during filesystem read delays.
- **Dependencies:** Completely replaces the fragile **multi-JSON checkpoint system** (`1_cleaned`, `2_grouped`, `3_routed`). Requires a **Unified `state.json`** as a hard dependency.

## 4. Timeline / Chronological Views
**Concept:**
A specialized projection of the document collection ordered entirely by time, mimicking the flow of incoming mail or a chronological ledger.
- **Table Stakes:** Extracting dates from metadata or LLM output; zero-padded prefixes to force exact chronological sorting in Windows File Explorer (e.g., `0001_Doc.lnk`, `0002_Doc.lnk`).
- **Differentiators:** Grouping by month/year subfolders automatically if the timeline gets too large.
- **Anti-features:** Physically duplicating files to create the timeline (as was done with the legacy `finalized.pdf`).
- **Complexity:** Low. Involves string manipulation, sorting arrays by date/ID, and batch shortcut creation.
- **Dependencies:** Deprecates the existing **`finalized.pdf` generation**. Adapts the existing **Append/Prepend logic** to control sorting direction (Prepend = newest first).

## 5. User Override Pinning
**Concept:**
When the bidirectional sync detects a user correction (e.g., a user moves a file from an AI-assigned "Unknown" folder to "Invoices"), the system must "pin" this decision. It flags the metadata so future automated pipeline runs do not revert the user's manual work.
- **Table Stakes:** Marking specific fields as `user_modified: true` or `pinned_category: "Invoices"` within the `state.json`. 
- **Differentiators:** Using pinned overrides as few-shot examples to improve the LLM categorization prompts on subsequent runs.
- **Anti-features:** Storing override state in memory or volatile temporary files; requiring the user to edit config files to fix an AI mistake.
- **Complexity:** Medium. State management must precisely lock attributes. The categorization pipeline must be updated to respect these locks.
- **Dependencies:** Relies on the **Bidirectional Sync engine** to trigger the pin. Must intercept the **LLM categorization** engine to bypass processing for pinned files.
