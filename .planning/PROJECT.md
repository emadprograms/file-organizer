# File Organizer Refactoring

## What This Is

A technical debt cleanup and refactoring effort for the file organizer project. The goal is to remove unused legacy code by tracing imports from the main entry point, break down bloated functions and files into smaller, more focused modules to improve maintainability, and implement logic-based modular refactoring (v2.0) utilizing YAML configuration instead of legacy anchor-based logic.

## Current Milestone: v3.0 Unified File-System UI & Append Mode

**Goal:** Integrate categorization logic into the main repository, enforce strict maintainability (types/docstrings), and introduce a "File-System UI" (FS-UI) allowing users to file documents purely by renaming files in an Inbox folder.

**Target features:**
- Codebase maintainability sweep (types, docstrings)
- System unification (port file-categorizer LLM logic)
- Configuration & explicit CLI modes (Create vs Append)
- Space-separated syntax parser for filenames
- File-System UI orchestration (rename loop)

## Core Value

Keep the codebase lean and maintainable without altering the existing correct functionality.

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

### Active

- Implement `config.yaml` for inbox/area mapping and explicit CLI modes (CONF-01)
- Build space-separated syntax parser for FS-UI (PARS-01)
- Implement FS-UI Append loop (`_Proposed` -> ` OK` -> Finalize) (FSUI-01)

### Out of Scope

- Adding new features or altering existing behavior (pure refactoring).
- Changing the underlying runtime or infrastructure.

## Current State

- ✅ Shipped v1.0 MVP.
- ✅ Shipped v1.1 Logging Overhaul.
- ✅ Shipped v1.2 Pipeline Resilience.
- ✅ Shipped v1.3 Routing Decoupling.
- ✅ Shipped v2.0 Logic-Based Modular Refactoring on 2026-07-17.
- ✅ Phase 20 complete — Codebase Maintainability Sweep (Types & Docs)
- ✅ Phase 21 complete — System Unification (file-categorizer porting)

## Context

- The codebase has been successfully cleaned of legacy code and refactored into a modular, maintainable structure.
- All processing logic is now decomposed into single-responsibility modules in `src/cleaning/` and `src/processing/`.
- Error handling is standardized via a custom exception hierarchy in `src/core/exceptions.py`.
- LLM resilience improved using `tenacity` for exponential backoff.
- The system now has a unified, hierarchical logging infrastructure with structured JSONL telemetry for LLM decisions.
- E2E testing overhauled using `pytest`, robust fixture directories, and LLM mocking via `unittest.mock`.
- The architecture is now cleanly separated into `core`, `utils`, `tenant_config`, `grouping`, `timeline`, and `routing`.

## Constraints

- **Functional Parity**: The refactoring must not break existing functionality or change the output format.
- **Maintainability**: The new modules should have clear, single responsibilities.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Break bloated code into new modules | Improves maintainability and file sizes over keeping them in the same file. | ✓ Completed (Phases 2, 3). Codebase is modular. |
| Trace imports from entry point | Safest way to identify truly unused legacy code without false positives. | ✓ Completed (Phase 1). Legacy and unused code removed. |
| Use dual-format logging | balances human readability in app.log with machine-searchability in debug.log. | ✓ Completed (Phase 4). |
| Switch to YAML-based tenant configuration | Allows for better future-proofing over fragile anchor-based legacy code. | ✓ Completed (v2.0). Anchor logic retained as a fallback. |
| Retain unittest in pytest suite | Avoids unnecessary refactoring churn when tests are functioning perfectly. | ✓ Completed (v2.0). Test suite uses both. |
| Hybrid functional/class architecture | Core pipeline is stateless (best for functional), FS-UI listener is stateful/long-running (best for OOP). | v3.0 decision: Keep pipeline functional, use classes for FS-UI orchestration (Phases 22-24). |

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-07-20*
