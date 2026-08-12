# Roadmap: File Organizer Refactoring

## Milestones

- 🏃 **v6.0 LLM Accuracy & Evaluation** — Phases 62-66 (Active)
- ⏸️ **v5.5 Pipeline Reversibility & Lossless Undo** — Phases 58-61 (Pivoted 2026-08-07)
- ✅ **v5.4 Architectural Consistency Refactor** — Phases 49-57 (shipped 2026-08-02)
- ✅ **v3.0 Unified File-System UI & Append Mode** — Phases 20-24.1 (shipped 2026-07-24)
- ✅ **v4.0 Architectural Cleanup** — Phases 25-29.1 (shipped 2026-07-31)
- ✅ **v5.0 Vault Architecture & Bidirectional Reconciliation** — Phases 30-35 (shipped 2026-08-01)
- ✅ **v5.1 Polishing & Migration Cleanup** — Phases 36-38 (shipped 2026-08-01)
- ✅ **v5.2 Deep Architecture Integrity & Verification** — Phases 39-42 (shipped 2026-08-01)
- ✅ **v5.3 Reconciliation Engine Upgrade** — Phases 43-48 (shipped 2026-08-01)

## Phases

<details open>
<summary>🏃 v6.0 LLM Accuracy & Evaluation (Phases 62-66) — ACTIVE</summary>

### Phase 62: OCR Golden Data Pre-processing
**Goal:** Generate the OCR `raw_dump.json` for the 4 Golden PDFs (Houses 1155, 1166, 1176, 1492) using Gemini (rotating 4 different API keys from `.env` and `.env2`). Save them in `tests/golden_data/` so subsequent prompt testing is fast and doesn't require re-uploading PDFs.

### Phase 63: Evaluation & Testing Harness
**Goal:** Build a script (`run_eval.py`) that uses the pre-processed `raw_dump.json` and grades the output against the Golden YAMLs to output a clear accuracy scoreboard.

### Phase 64: Name Canonicalization (Completed)
**Goal:** (Using Gemma-4-31B) Recursively tweak prompts and logic until we hit 100% accuracy in mapping extracted names to existing `tenants.yaml` keys without creating duplicate/random folders.
*Status: Hit 99.07% practical accuracy on clean dataset (1492).*

### Phase 65: Integrate Pass 2 Categorization & Comprehensive Testing (Completed)
**Goal:** Integrate the newly perfected "Pass 2 Fine Categorization" into the main production pipeline, and write comprehensive tests for it.

### Phase 66: OCR Letter Continuation Detection (is_continuation)
**Goal:** Implement the `is_continuation` fix for the OCR pass so that pages lacking subjects/addressees are marked as continuations.

### Phase 67: Test Suite Cleanup & Missing Imports
**Goal:** Fix pre-existing `NameError` bugs in `router.py` and align tests with Phase 64 & 65 changes to return the test suite to 100% green.

</details>

<details>
<summary>⏸️ v5.5 Pipeline Reversibility & Lossless Undo (Phases 58-61) — PIVOTED</summary>

### Phase 58: Lossless Undo Command
- [x] Implement `python src/main.py undo <target_dir>`
- [x] Read `_state.json` routed documents
- [x] Reconstruct `<house_id>.pdf` perfectly via `fitz` using vault files
- [x] Wipe target_dir (except reconstructed PDF)

### Phase 59: _report.json Paradigm Shift
**Goal:** Move raw AI extraction to `.raw_dump.json`. Generate a brand new `_report.json` at the end of generation (for both `create` and `append`) that perfectly mirrors the Timeline View's grouped structure.

### Phase 60: Migration Script (Completed)
**Goal:** Build a script to ingest old messy `_report.json` files, generate the new chronological format, and bring legacy houses up to the v5.5 standard.

### Phase 61: Test Suite Update (Completed)
**Goal:** Add E2E tests for the `undo` command, update existing assertions for the new `_report.json` format, and add migration tests.

</details>

<details>
<summary>✅ v3.0 Unified File-System UI & Append Mode (Phases 20-24.1) — SHIPPED 2026-07-24</summary>

- [x] Phase 20: Codebase Maintainability Sweep (3/3 plans) — completed 2026-07-18
- [x] Phase 21: System Unification (1/1 plan) — completed 2026-07-20
- [x] Phase 22: Configuration and CLI Modes (3/3 plans) — completed 2026-07-20
- [x] Phase 23: Inbox Parsing and Syntax (2/2 plans) — completed 2026-07-20
- [x] Phase 24: FS-UI Orchestration (4/4 plans) — completed 2026-07-20
- [x] Phase 24.1: Update test suite and fixtures for Phase 24 (4/4 plans) — completed 2026-07-23

</details>

<details>
<summary>✅ v4.0 Architectural Cleanup (Phases 25-29.1) — SHIPPED 2026-07-31</summary>

- [x] Phase 25: Extract Presentation Logic from `core/` (ARCH-01) - completed 2026-07-24
- [x] Phase 26: Rename `fs_ui/` to `watcher/` (ARCH-02) - completed 2026-07-24
- [x] Phase 27: Disambiguate Reconciliation Modules (ARCH-03) - completed 2026-07-24
- [x] Phase 28: Clean Up `main.py` Dead Imports (ARCH-04) - completed 2026-07-24
- [x] Phase 29: Audit Test Mock Patch Targets (ARCH-05) - completed 2026-07-24
- [x] Phase 29.1: Fix Append-Mode Finalize Bugs (URGENT) - completed 2026-07-31

</details>

<details>
<summary>✅ v5.0 Vault Architecture & Bidirectional Reconciliation (Phases 30-35) — SHIPPED 2026-08-01</summary>

See [.planning/milestones/v5.0-ROADMAP.md](milestones/v5.0-ROADMAP.md) for full phase details.

</details>

<details>
<summary>✅ v5.1 Polishing & Migration Cleanup (Phases 36-38) — SHIPPED 2026-08-01</summary>

See [.planning/milestones/v5.1-ROADMAP.md](milestones/v5.1-ROADMAP.md) for full phase details.

</details>

<details>
<summary>✅ v5.2 Deep Architecture Integrity & Verification (Phases 39-42) — SHIPPED 2026-08-01</summary>

### Phase 39: Verification Module Scaffolding & CLI Integration

**Requirements:** REQ-01
**Success Criteria:** `src/core/verification.py` is created. `main.py` CLI exposes `file-organizer verify`. Basic structural checking is wired up.

### Phase 40: Vault & Shortcut Resolution Engine

**Requirements:** REQ-02
**Success Criteria:** The verifier recursively parses `.lnk` files in categorized directories and `[Timeline View]`, validating their absolute targets against the vault.

### Phase 41: State & YAML Integrity Rules

**Requirements:** REQ-03, REQ-04
**Success Criteria:** The verifier cross-references `state.json` against actual folder layout. Orphan PDFs in the vault are detected. Ghost legacy JSONs and physical PDFs outside the vault are flagged. Tenant structures match `tenants.yaml`.

### Phase 42: Comprehensive Test Suite

**Requirements:** REQ-05
**Success Criteria:** `pytest` tests are added for the verification module handling various valid and corrupt state scenarios.

</details>

<details>
<summary>✅ v5.3 Reconciliation Engine Upgrade (Phases 43-48) — SHIPPED 2026-08-01</summary>

See [.planning/milestones/v5.3-ROADMAP.md](milestones/v5.3-ROADMAP.md) for full phase details.

</details>

<details>
<summary>✅ v5.4 Architectural Consistency Refactor (Phases 49-57) — SHIPPED 2026-08-02</summary>

See [.planning/milestones/v5.4-ROADMAP.md](milestones/v5.4-ROADMAP.md) for full phase details.

</details>


## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 20. Codebase Maintainability Sweep | v3.0 | 3/3 | Complete | 2026-07-18 |
| 21. System Unification | v3.0 | 1/1 | Complete | 2026-07-20 |
| 22. Configuration and CLI Modes | v3.0 | 3/3 | Complete | 2026-07-20 |
| 23. Inbox Parsing and Syntax | v3.0 | 2/2 | Complete | 2026-07-20 |
| 24. FS-UI Orchestration | v3.0 | 4/4 | Complete | 2026-07-20 |
| 24.1. Test Suite & Fixtures Update | v3.0 | 4/4 | Complete | 2026-07-23 |
| 25. Extract Presentation from core/ | v4.0 | 1/1 | Complete | 2026-07-24 |
| 26. Rename fs_ui/ to watcher/ | v4.0 | 1/1 | Complete | 2026-07-24 |
| 27. Disambiguate Reconciliation | v4.0 | 1/1 | Complete | 2026-07-24 |
| 28. Clean Up main.py Imports | v4.0 | 1/1 | Complete | 2026-07-24 |
| 29. Audit Test Mock Targets | v4.0 | 1/1 | Complete | 2026-07-24 |
| 29.1. Fix Append-Mode Finalize Bugs | v4.0 | 1/1 | Complete | 2026-07-31 |
| 30. Unified State Foundation | v5.0 | 1/1 | Complete    | 2026-07-31 |
| 31. Vault Core & Shortcut Utility | v5.0 | 1/1 | Complete    | 2026-07-31 |
| 32. Pipeline Migration | v5.0 | 1/0 | Complete    | 2026-07-31 |
| 33. Bidirectional Reconciliation Engine | v5.0 | 1/1 | Complete    | 2026-07-31 |
| 34. Prepend Mode | v5.0 | 1/0 | Complete    | 2026-07-31 |
| 35. Migration Script | v5.0 | 1/0 | Complete    | 2026-07-31 |
| 36. Environment & E2E Testing | v5.1 | 1/1 | Complete | 2026-08-01 |
| 37. Timeline View UX Improvements | v5.1 | 1/1 | Complete | 2026-08-01 |
| 38. Unified State Migration | v5.1 | 1/1 | Complete | 2026-08-01 |
| 39. Verification Scaffolding | v5.2 | 1/1 | Complete | 2026-08-01 |
| 40. Vault & Shortcut Engine | v5.2 | 1/1 | Complete | 2026-08-01 |
| 41. State & YAML Rules | v5.2 | 1/1 | Complete | 2026-08-01 |
| 42. Comprehensive Test Suite | v5.2 | 1/1 | Complete | 2026-08-01 |
| 43. Ghost File Adoption & Raw PDF Ingestion | v5.3 | 1/1 | Complete | 2026-08-01 |
| 44. User Deletion & Orphan Cleanup | v5.3 | 1/1 | Complete | 2026-08-01 |
| 45. Duplicate Shortcuts & Renamed Shortcuts | v5.3 | 1/1 | Complete | 2026-08-01 |
| 46. Auto-Verification & Reconciliation Report | v5.3 | 1/1 | Complete | 2026-08-01 |
| 47. Reconciliation Test Suite | v5.3 | 1/1 | Complete | 2026-08-01 |
| 48. Data Preservation & Verification Overhaul | v5.3 | 1/1 | Complete | 2026-08-01 |
| 49. 1-to-Many Shortcut Mapping | v5.4 | 1/1 | Complete | 2026-08-01 |
| 50. Cross-House Contamination Immunity | v5.4 | 1/1 | Complete | 2026-08-01 |
| 51. Phase 51 | v5.4 | 1/1 | Complete | 2026-08-02 |
| 52. Phase 52 | v5.4 | 1/1 | Complete | 2026-08-02 |
| 53. Phase 53 | v5.4 | 1/1 | Complete | 2026-08-02 |
| 54. Phase 54 | v5.4 | 1/1 | Complete | 2026-08-02 |
| 55. Phase 55 | v5.4 | 1/1 | Complete | 2026-08-02 |
| 56. Phase 56 | v5.4 | 1/1 | Complete | 2026-08-02 |
| 57. Phase 57 | v5.4 | 1/1 | Complete | 2026-08-02 |
| 58. Lossless Undo Command | v5.5 | 1/1 | Complete | 2026-08-07 |
| 59. _report.json Paradigm Shift | v5.5 | 1/1 | Complete | 2026-08-07 |
| 60. Migration Script | v5.5 | 1/1 | Complete | 2026-08-07 |
| 61. Test Suite Update | v5.5 | 1/1 | Complete | 2026-08-07 |
| 62. OCR Golden Data Pre-processing | v6.0 | 1/1 | Complete | 2026-08-10 |
| 63. Evaluation & Testing Harness | v6.0 | 1/1 | Complete | 2026-08-10 |
| 64. Name Canonicalization | v6.0 | 1/1 | Complete | 2026-08-10 |
| 65. Integrate Pass 2 Categorization | v6.0 | 1/1 | Complete | 2026-08-11 |
| 65. Integrate Pass 2 Categorization | v6.0 | 1/1 | Complete | 2026-08-11 |
| 66. OCR Letter Continuation Detection | v6.0 | 1/1 | Complete | 2026-08-12 |
| 67. Test Suite Cleanup & Missing Imports | v6.0 | 0/1 | Active | |



