# Vault Architecture & Bidirectional Reconciliation — Architecture Research

## 1. Existing Modules (Modify vs Replace vs Untouched)

### Modified
- **`src/main.py`**: Update CLI commands (rename "append" to "prepend") and adapt pipeline invocation to the new state and vault architecture.
- **`src/pipeline/runner.py`**: Update `run_cleaning_pass`, `run_grouping_pass`, `run_routing_pass`, and `run_generation_pass` to read/write from a unified `state.json` rather than separate checkpoint files. `run_generation_pass` will stop building `finalized.pdf` and instead trigger Vault storage and shortcut generation.
- **`src/timeline/core.py`**: `FileOrganizer` must be updated to extract PDFs into the immutable Vault rather than directly into user-facing folders, and generate Windows `.lnk` shortcuts instead.
- **`src/reconcile/core.py`**: Rewrite to support bidirectional sync (detecting user moves via shortcut paths) instead of just one-way tenant updates.

### Replaced/Deprecated
- The multi-JSON checkpoint files (`1_cleaned.json`, `2_grouped.json`, `3_routed_and_finalized.json`) are replaced by a single unified `state.json`.
- `finalized.pdf` generation (using PyMuPDF `fitz` TOC features) is completely replaced by the `00_Timeline_View/` folder containing chronological numbered shortcuts.

### Untouched
- **`src/categorization/`** and `report.json` generation: Per constraints, the LLM vision and extraction layer remains entirely untouched.
- **`src/grouping/`** (fuzzy matching, logic): Explicitly marked out of scope for this milestone.
- **`src/routing/`** logic: Core mapping logic remains the same, only the persistence mechanism changes.

## 2. New Modules/Packages to Create
- **`src/vault/`** (Vault Manager): A new package to handle assigning unique document IDs, immutably storing extracted PDFs in a hidden/secured vault directory, and enforcing the "store once, never move" rule.
- **`src/utils/shortcuts.py`** (Windows Linker): A utility module specifically for creating Windows `.lnk` files that point to the Vault PDFs.
- **`src/core/state.py`** (Unified State Manager): A module to manage interactions with the unified `state.json`, including applying updates per phase and handling user-pinned overrides.

## 3. Data Flow Changes (4-pass to Unified State)
- **Current Flow:** Raw PDF → Categorization generates `report.json` → Cleaning generates `1_cleaned.json` → Grouping generates `2_grouped.json` → Routing generates `3_routed...json`. Physical PDF segments are written directly to `House/Tenant/Topic/doc.pdf` and merged into `finalized.pdf`.
- **New Flow:** Raw PDF → Categorization generates `report.json` (untouched). The pipeline then initializes a single `state.json`. Cleaning, Grouping, and Routing update this single state in-memory and flush it. Finally, generation extracts physical PDF segments strictly into the Vault (`Vault/doc_id.pdf`), and creates lightweight Windows `.lnk` shortcuts in both the hierarchical user folders (`House/Tenant/Topic/doc.lnk`) and the chronological timeline folder (`House/00_Timeline_View/01_doc.lnk`).

## 4. Suggested Build Order to Minimize Integration Risk
1. **Phase 1: Unified State Foundation:** Refactor `pipeline/runner.py` to use a single `state.json` struct instead of 3 separate files. Ensure data consistency before touching the filesystem.
2. **Phase 2: Vault Core & Shortcut Utility:** Build the `src/vault/` logic and the Windows `.lnk` generator. Add unit tests for shortcut target resolution.
3. **Phase 3: FileOrganizer Migration:** Modify `timeline/core.py` to write extracted PDFs to the Vault and deploy `.lnk` shortcuts to the user-facing folders and the new `Timeline_View` folder, dropping `finalized.pdf`.
4. **Phase 4: Bidirectional Reconciliation Engine:** Rewrite `reconcile/core.py` to read shortcut targets, detect user overrides (shortcuts moved to new folders), and pin these overrides in `state.json`.
5. **Phase 5: Prepend Mode & Polish:** Rename append to prepend across `main.py` and the `watcher` package, and finalize integrations.

## 5. Reconciliation Engine Structure (Bidirectional Sync)
- **Primary Key:** The Vault Document ID (derived from the shortcut's target path).
- **State vs. Filesystem:** The engine will scan the user-facing folder hierarchy for `.lnk` shortcuts. It will compare the physical location of the shortcut (e.g., `Tenant A/Taxes/doc.lnk`) against the expected location in `state.json`.
- **User Override Detection:** If a shortcut is found in a different topic or tenant folder than what `state.json` dictates, the engine assumes the user intentionally moved it. It must update `state.json` with the new route and set a "pinned" flag for that document.
- **System Updates:** If the pipeline/config updates (e.g., tenant name change in YAML) and the document is *not* pinned by the user, the engine generates/moves the shortcut to the newly computed path.
