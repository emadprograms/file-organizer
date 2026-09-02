# File Organizer Refactoring

## What This Is

A document management system that processes scanned Arabic PDFs, categorizes them using LLM vision, groups related pages, and organizes them into a structured folder hierarchy per tenant household. The system runs on Windows and uses a Vault-based architecture with shortcuts for file organization and bidirectional reconciliation.

## Current Milestone: v9.0 Hierarchical Web Dashboard

**Goal:** Completely revamp the Web GUI into a hierarchical dashboard with global search functionality mirroring the native disk structure.

**Target features:**
- Hierarchical drill-down sidebar (Areas -> Houses -> Tenants/Timelines) reading from `areas_root_path`.
- Top navigation search bar for instant jump by house number or person name.
- Strict TDD for backend (pytest directory-scanning and search APIs).
- Strict TDD for frontend (Playwright UI hierarchy E2E tests).

## Core Value

Documents are safely stored once in an immutable vault; all organization is done via lightweight shortcuts that can be freely rearranged by the user without risk of data loss.

## Requirements

### Validated

- âœ“ 1-to-Many Shortcut Mapping (REQ-01) (Phase 49) â€” v5.4
- âœ“ Cross-House Contamination Immunity (REQ-02) (Phase 50) â€” v5.4
- âœ“ Multi-Page Raw PDF Ingestion (REQ-03) (Phase 51) â€” v5.4
- âœ“ Corrupted Vault File Safeguards (REQ-04) (Phase 52) â€” v5.4
- âœ“ Nested Folder Trap (REQ-05) (Phase 53) â€” v5.4
- âœ“ Tenant Root Folder Renaming (REQ-06) (Phase 54) â€” v5.4
- âœ“ Shortcut Target Hijack / Corruption (REQ-07) (Phase 55) â€” v5.4
- âœ“ Idempotency Guarantee (REQ-08) (Phase 56) â€” v5.4
- âœ“ File Locking Resilience (REQ-09) (Phase 57) â€” v5.4
- âœ“ Vault storage system with unique document IDs (VAULT) (Phase 30-35) â€” v5.0
- âœ“ Windows .lnk shortcut generation replacing direct file placement (LNK) (Phase 30-35) â€” v5.0
- âœ“ Unified state.json replacing multi-JSON checkpoint system (STATE) (Phase 30-35) â€” v5.0
- âœ“ Timeline View folder with chronological numbered shortcuts (TIMELINE) (Phase 30-35) â€” v5.0
- âœ“ Bidirectional reconciliation with user override detection and pinning (RECON) (Phase 30-35) â€” v5.0
- âœ“ Rename append â†’ prepend mode and adapt to new architecture (PREPEND) (Phase 30-35) â€” v5.0
- âœ“ Identify and remove all unreachable legacy code that is not imported or used by the main application flow. (Phase 01) â€” v1.0
- âœ“ Refactor `src/cleaning.py` into separate focused modules based on responsibility. (Phase 02) â€” v1.0
- âœ“ Refactor bloated files in `src/processing/` into smaller, single-responsibility modules. (Phase 03) â€” v1.0
- âœ“ Split oversized functions across the application into smaller functions. (Phase 03) â€” v1.0
- âœ“ Implement isolated application logging to remove third-party library noise. (Phase 04) â€” v1.1
- âœ“ Establish a unified `LogContext` to prevent fragmented run directories. (Phase 04) â€” v1.1
- âœ“ Implement dual-format logging: Plain Text for `app.log` and JSON for `debug.log`. (Phase 04) â€” v1.1
- âœ“ Update all modules to use hierarchical logger naming (`file_organizer.module`). (Phase 05) â€” v1.1
- âœ“ Rate Limiting & Router Safety Net (RES) â€” v1.2
- âœ“ Chunk State Management (GRP) â€” v1.2
- âœ“ "True Until Proven Guilty" Grouping Logic (PRMPT) â€” v1.2
- âœ“ Anti-Hallucination Schema Enforcement (SCHM) â€” v1.2
- âœ“ Modular restructuring (`core`, `utils`, `tenant_config`, `grouping`, `timeline`, `routing`) (ARCH) â€” v2.0
- âœ“ YAML loading and tenant name extraction (YAML) â€” v2.0
- âœ“ Replace anchor logic with YAML-based LLM Name Matching in Pass 1 (PIPE) â€” v2.0
- âœ“ Add type hinting and docstrings across all v2.0 modules (MAINT-01) (Phase 20) â€” v3.0
- âœ“ Port file-categorizer OCR and Gemini 3.1 FL logic to main repository (CAT-01) (Phase 21) â€” v3.0
- âœ“ Implement early bypass for existing categorized reports (CAT-02) (Phase 21) â€” v3.0
- âœ“ Implement `config.yaml` for inbox/area mapping and explicit CLI modes (CONF-01, CONF-02, CONF-03) (Phase 22) â€” v3.0
- âœ“ Build space-separated syntax parser & resolver for FS-UI (FSUI-01, FSUI-02, FSUI-03) (Phase 23) â€” v3.0
- âœ“ Implement FS-UI Append loop (`_Proposed` -> ` OK` -> Finalize) (FSUI-04, FSUI-05, FSUI-06) (Phase 24) â€” v3.0
- âœ“ Extract `core/ui.py` to `src/presentation/ui.py` â€” presentation logic out of domain core (ARCH-01) (Phase 25) â€” v4.0
- âœ“ Rename `fs_ui/` â†’ `watcher/` â€” accurate naming for file watcher package (ARCH-02) (Phase 26) â€” v4.0
- âœ“ Rename `timeline/reconciliation.py` â†’ `timeline/page_integrity.py` â€” disambiguate from `reconcile/core.py` (ARCH-03) (Phase 27) â€” v4.0
- âœ“ Remove dead `fitz`/`json` imports from `main.py` after runner extraction (ARCH-04) (Phase 28) â€” v4.0
- âœ“ Audit all test mock `@patch()` targets for import-site correctness (ARCH-05) (Phase 29) â€” v4.0

- âœ“ Add `pylnk3` to requirements and fix the test environment (ENV-01) â€” v5.1
- âœ“ Timeline View shortcut prefixes reflect page index (TIMELINE-05) â€” v5.1
- âœ“ Migration script consolidates legacy JSONs into `state.json` and deletes old checkpoints (MIGRATE-04) â€” v5.1
- âœ“ Build E2E test suite targeting `D:\Areas` (TEST-01) â€” v5.1

### Active

- âœ“ Ghost file adoption into state.json during reconciliation (RECON-ADOPT) (Phase 43) â€” v5.3
- âœ“ User deletion detection and vault trash cleanup (RECON-DELETE) (Phase 44) â€” v5.3
- âœ“ Raw PDF ingestion into vault from categorized folders (RECON-INGEST) (Phase 43) â€” v5.3
- âœ“ Duplicate shortcut support (1-to-many vault mapping) (RECON-DUP) (Phase 45) â€” v5.3
- âœ“ Renamed shortcut detection and state sync (RECON-RENAME) (Phase 45) â€” v5.3
- âœ“ Auto-verification after reconciliation (RECON-VERIFY) (Phase 46) â€” v5.3
- âœ“ Reconciliation report generation (RECON-REPORT) (Phase 46) â€” v5.3
- âœ“ Comprehensive pytest test suite for reconciliation edge cases (RECON-TEST) (Phase 47) â€” v5.3
- âœ“ Data Preservation & Verification Overhaul (Many-to-One and Immutable Page Audit) (REQ-09) (Phase 48) â€” v5.3

### Active

- [ ] Perfect Idempotent Reconciliation (Zero-Delta on fresh output) (REQ-01) (Phase 68) â€” v6.1
- [ ] Timeline View Sort Order Consistency (REQ-02) (Phase 69) â€” v6.1
- [ ] Fix phantom shortcut rewrites (REQ-03) (Phase 70) â€” v6.1

### Shipped in v6.0
- âœ“ OCR Golden Data Pre-processing (REQ-01) (Phase 62) â€” v6.0
- âœ“ Automated Evaluation Harness (REQ-02) (Phase 63) â€” v6.0
- âœ“ Name Canonicalization Accuracy (REQ-03) (Phase 64) â€” v6.0
- âœ“ Pass 2 Fine Categorization (REQ-04) (Phase 65) â€” v6.0
- âœ“ OCR Letter Continuation Detection (REQ-05) (Phase 66) â€” v6.0
- âœ“ Test Suite Cleanup (Phase 67) â€” v6.0

### Out of Scope

- macOS support â€” this milestone targets Windows only (`.lnk` shortcuts).

## Current State

- âœ… Shipped v1.0 MVP.
- âœ… Shipped v1.1 Logging Overhaul.
- âœ… Shipped v1.2 Pipeline Resilience.
- âœ… Shipped v1.3 Routing Decoupling.
- âœ… Shipped v2.0 Logic-Based Modular Refactoring on 2026-07-17.
- âœ… Shipped v3.0 Unified File-System UI & Append Mode on 2026-07-24.
- âœ… Shipped v4.0 Architectural Cleanup on 2026-07-24.
- âœ… Shipped v5.0 Vault Architecture & Bidirectional Reconciliation on 2026-08-01.
- âœ… Shipped v5.1 Polishing & Migration Cleanup on 2026-08-01.
- âœ… Shipped v5.2 Deep Architecture Integrity & Verification on 2026-08-01.
- âœ… Shipped v5.3 Reconciliation Engine Upgrade on 2026-08-01.
- âœ… Shipped v5.4 Architectural Consistency Refactor on 2026-08-02.
- â ¸ï¸  Pivoted from v5.5 (Lossless Undo) to v6.0 (LLM Accuracy) on 2026-08-10.
- âœ… Shipped v6.0 LLM Accuracy & Evaluation on 2026-08-12.
- âœ… Shipped v8.0 Web-Based File Viewer on 2026-09-02.

## Context

- The codebase has been through 4 milestones of refactoring and is cleanly modular.
- The current storage model places physical PDFs directly in user-facing folders, making reconciliation fragile.
- Multiple JSON checkpoint files (`1_cleaned`, `2_grouped`, `3_routed`) drift out of sync with each other and the filesystem.
- Manual user corrections (dragging files to fix AI routing mistakes) permanently break the JSON state.
- The `finalized.pdf` duplicates all documents, wasting significant disk space.
- Target deployment is Windows â€” all file operations must use Windows shortcuts (`.lnk`), not macOS symlinks.
- The LLM extraction layer (categorization, `report.json` generation) remains unchanged.

## Constraints

- **Windows Target**: All file operations must use Windows `.lnk` shortcuts, not macOS symlinks or aliases.
- **LLM Layer Untouched**: The categorization engine and `report.json` generation must not change.
- **Vault Immutability**: Once a PDF enters the vault, it is never moved or renamed. All organization is done via shortcuts.
- **Backward Compatibility**: Existing processed houses should be migratable to the new vault system.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Break bloated code into new modules | Improves maintainability and file sizes over keeping them in the same file. | âœ“ Completed (Phases 2, 3). Codebase is modular. |
| Trace imports from entry point | Safest way to identify truly unused legacy code without false positives. | âœ“ Completed (Phase 1). Legacy and unused code removed. |
| Use dual-format logging | balances human readability in app.log with machine-searchability in debug.log. | âœ“ Completed (Phase 4). |
| Switch to YAML-based tenant configuration | Allows for better future-proofing over fragile anchor-based legacy code. | âœ“ Completed (v2.0). Anchor logic retained as a fallback. |
| Retain unittest in pytest suite | Avoids unnecessary refactoring churn when tests are functioning perfectly. | âœ“ Completed (v2.0). Test suite uses both. |
| Hybrid functional/class architecture | Core pipeline is stateless (best for functional), FS-UI listener is stateful/long-running (best for OOP). | v3.0 decision: Keep pipeline functional, use classes for FS-UI orchestration (Phases 22-24). |
| Surgical cleanup over full restructuring | Adding `domain/` and `infra/` wrapper layers would add nesting without benefit in a 14-package project. Targeted renames and moves give the same clarity. | v4.0 decision: 5-point surgical cleanup, no deep nesting. |
| Vault + Shortcuts over direct file placement | Decouples physical storage from organization. User can freely rearrange shortcuts without risk of data loss. Eliminates finalized.pdf duplication. | v5.0 decision: Vault stores originals, shortcuts provide views. |
| Unified state.json over multi-JSON checkpoints | Single source of truth eliminates drift between 1_cleaned, 2_grouped, 3_routed JSONs. | v5.0 decision: One state.json per house, report.json preserved as raw LLM dump. |
| Bidirectional reconciliation over one-way sync | System detects manual user file moves and pins them, instead of overwriting user corrections. | v5.0 decision: Filesystem is a valid source of user intent. |
| Timeline View folder over finalized.pdf | Chronological numbered shortcuts eliminate disk space duplication while preserving the reading experience. | v5.0 decision: Replace finalized.pdf with 00_Timeline_View/. |
| Reconciliation as the system's immune system | Ghost file adoption, deletion handling, raw PDF ingestion, and duplicate support belong in the reconciler, not in migration scripts. The reconciler is the permanent sync engine. | v5.3 decision: Reconciler guarantees 100% state-to-filesystem harmony. |

| True 1-to-Many Shortcut Mapping | Splitting pages across shortcuts is a hack that breaks architectural purity. A 2-page document should always be 2 pages, even if it has 5 shortcuts. | v5.4 decision: Decouple Pages from Shortcuts completely. |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-02 - Transitioning to v9.0: Hierarchical Web Dashboard.*
