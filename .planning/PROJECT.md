# File Organizer Refactoring

## What This Is

A document management system that processes scanned Arabic PDFs, categorizes them using LLM vision, groups related pages, and organizes them into a structured folder hierarchy per tenant household. The system runs on Windows and uses a Vault-based architecture with shortcuts for file organization and bidirectional reconciliation.

## Current Milestone: v5.0 Vault Architecture & Bidirectional Reconciliation

**Goal:** Replace the fragile multi-JSON checkpoint system with an ID-based Vault storage architecture using Windows shortcuts, enabling bidirectional reconciliation where manual user corrections are automatically detected and preserved.

**Target features:**
- Vault storage system with unique document IDs
- Windows `.lnk` shortcut generation (replacing direct file placement)
- Unified `state.json` replacing `1_cleaned`, `2_grouped`, `3_routed` JSONs
- Timeline View folder (chronological numbered shortcuts replacing `finalized.pdf`)
- Bidirectional reconciliation with user override detection and pinning
- Rename "append" → "prepend" mode and adapt to new architecture

## Core Value

Documents are safely stored once in an immutable vault; all organization is done via lightweight shortcuts that can be freely rearranged by the user without risk of data loss.

## Requirements

### Validated

- ✓ Identify and remove all unreachable legacy code that is not imported or used by the main application flow. (Phase 01) — v1.0
- ✓ Refactor `src/cleaning.py` into separate focused modules based on responsibility. (Phase 02) — v1.0
- ✓ Refactor bloated files in `src/processing/` into smaller, single-responsibility modules. (Phase 03) — v1.0
- ✓ Split oversized functions across the application into smaller functions. (Phase 03) — v1.0
- ✓ Implement isolated application logging to remove third-party library noise. (Phase 04) — v1.1
- ✓ Establish a unified `LogContext` to prevent fragmented run directories. (Phase 04) — v1.1
- ✓ Implement dual-format logging: Plain Text for `app.log` and JSON for `debug.log`. (Phase 04) — v1.1
- ✓ Update all modules to use hierarchical logger naming (`file_organizer.module`). (Phase 05) — v1.1
- ✓ Rate Limiting & Router Safety Net (RES) — v1.2
- ✓ Chunk State Management (GRP) — v1.2
- ✓ "True Until Proven Guilty" Grouping Logic (PRMPT) — v1.2
- ✓ Anti-Hallucination Schema Enforcement (SCHM) — v1.2
- ✓ Modular restructuring (`core`, `utils`, `tenant_config`, `grouping`, `timeline`, `routing`) (ARCH) — v2.0
- ✓ YAML loading and tenant name extraction (YAML) — v2.0
- ✓ Replace anchor logic with YAML-based LLM Name Matching in Pass 1 (PIPE) — v2.0
- ✓ Add type hinting and docstrings across all v2.0 modules (MAINT-01) (Phase 20) — v3.0
- ✓ Port file-categorizer OCR and Gemini 3.1 FL logic to main repository (CAT-01) (Phase 21) — v3.0
- ✓ Implement early bypass for existing categorized reports (CAT-02) (Phase 21) — v3.0
- ✓ Implement `config.yaml` for inbox/area mapping and explicit CLI modes (CONF-01, CONF-02, CONF-03) (Phase 22) — v3.0
- ✓ Build space-separated syntax parser & resolver for FS-UI (FSUI-01, FSUI-02, FSUI-03) (Phase 23) — v3.0
- ✓ Implement FS-UI Append loop (`_Proposed` -> ` OK` -> Finalize) (FSUI-04, FSUI-05, FSUI-06) (Phase 24) — v3.0
- ✓ Extract `core/ui.py` to `src/presentation/ui.py` — presentation logic out of domain core (ARCH-01) (Phase 25) — v4.0
- ✓ Rename `fs_ui/` → `watcher/` — accurate naming for file watcher package (ARCH-02) (Phase 26) — v4.0
- ✓ Rename `timeline/reconciliation.py` → `timeline/page_integrity.py` — disambiguate from `reconcile/core.py` (ARCH-03) (Phase 27) — v4.0
- ✓ Remove dead `fitz`/`json` imports from `main.py` after runner extraction (ARCH-04) (Phase 28) — v4.0
- ✓ Audit all test mock `@patch()` targets for import-site correctness (ARCH-05) (Phase 29) — v4.0

### Active

- [ ] Vault storage system with unique document IDs (VAULT)
- [ ] Windows `.lnk` shortcut generation replacing direct file placement (LNK)
- [ ] Unified `state.json` replacing multi-JSON checkpoint system (STATE)
- [ ] Timeline View folder with chronological numbered shortcuts (TIMELINE)
- [ ] Bidirectional reconciliation with user override detection and pinning (RECON)
- [ ] Rename append → prepend mode and adapt to new architecture (PREPEND)

### Out of Scope

- Grouping logic changes — fixing how pages are merged into documents is deferred to a future milestone.
- Name canonicalization — fixing how family members are grouped requires a separate phase with LLM prompt redesign.
- macOS support — this milestone targets Windows only (`.lnk` shortcuts).

## Current State

- ✅ Shipped v1.0 MVP.
- ✅ Shipped v1.1 Logging Overhaul.
- ✅ Shipped v1.2 Pipeline Resilience.
- ✅ Shipped v1.3 Routing Decoupling.
- ✅ Shipped v2.0 Logic-Based Modular Refactoring on 2026-07-17.
- ✅ Shipped v3.0 Unified File-System UI & Append Mode on 2026-07-24.
- ✅ Shipped v4.0 Architectural Cleanup on 2026-07-24.
- 🚧 v5.0 Vault Architecture & Bidirectional Reconciliation started 2026-07-31.

## Context

- The codebase has been through 4 milestones of refactoring and is cleanly modular.
- The current storage model places physical PDFs directly in user-facing folders, making reconciliation fragile.
- Multiple JSON checkpoint files (`1_cleaned`, `2_grouped`, `3_routed`) drift out of sync with each other and the filesystem.
- Manual user corrections (dragging files to fix AI routing mistakes) permanently break the JSON state.
- The `finalized.pdf` duplicates all documents, wasting significant disk space.
- Target deployment is Windows — all file operations must use Windows shortcuts (`.lnk`), not macOS symlinks.
- The LLM extraction layer (categorization, `report.json` generation) remains unchanged.

## Constraints

- **Windows Target**: All file operations must use Windows `.lnk` shortcuts, not macOS symlinks or aliases.
- **LLM Layer Untouched**: The categorization engine and `report.json` generation must not change.
- **Vault Immutability**: Once a PDF enters the vault, it is never moved or renamed. All organization is done via shortcuts.
- **Backward Compatibility**: Existing processed houses should be migratable to the new vault system.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Break bloated code into new modules | Improves maintainability and file sizes over keeping them in the same file. | ✓ Completed (Phases 2, 3). Codebase is modular. |
| Trace imports from entry point | Safest way to identify truly unused legacy code without false positives. | ✓ Completed (Phase 1). Legacy and unused code removed. |
| Use dual-format logging | balances human readability in app.log with machine-searchability in debug.log. | ✓ Completed (Phase 4). |
| Switch to YAML-based tenant configuration | Allows for better future-proofing over fragile anchor-based legacy code. | ✓ Completed (v2.0). Anchor logic retained as a fallback. |
| Retain unittest in pytest suite | Avoids unnecessary refactoring churn when tests are functioning perfectly. | ✓ Completed (v2.0). Test suite uses both. |
| Hybrid functional/class architecture | Core pipeline is stateless (best for functional), FS-UI listener is stateful/long-running (best for OOP). | v3.0 decision: Keep pipeline functional, use classes for FS-UI orchestration (Phases 22-24). |
| Surgical cleanup over full restructuring | Adding `domain/` and `infra/` wrapper layers would add nesting without benefit in a 14-package project. Targeted renames and moves give the same clarity. | v4.0 decision: 5-point surgical cleanup, no deep nesting. |
| Vault + Shortcuts over direct file placement | Decouples physical storage from organization. User can freely rearrange shortcuts without risk of data loss. Eliminates finalized.pdf duplication. | v5.0 decision: Vault stores originals, shortcuts provide views. |
| Unified state.json over multi-JSON checkpoints | Single source of truth eliminates drift between 1_cleaned, 2_grouped, 3_routed JSONs. | v5.0 decision: One state.json per house, report.json preserved as raw LLM dump. |
| Bidirectional reconciliation over one-way sync | System detects manual user file moves and pins them, instead of overwriting user corrections. | v5.0 decision: Filesystem is a valid source of user intent. |
| Timeline View folder over finalized.pdf | Chronological numbered shortcuts eliminate disk space duplication while preserving the reading experience. | v5.0 decision: Replace finalized.pdf with 00_Timeline_View/. |

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-07-31 — v5.0 Vault Architecture & Bidirectional Reconciliation milestone started*
