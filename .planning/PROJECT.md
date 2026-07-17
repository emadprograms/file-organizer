# File Organizer Refactoring

## What This Is

A technical debt cleanup and refactoring effort for the file organizer project. The goal is to remove unused legacy code by tracing imports from the main entry point, and to break down bloated functions and files into smaller, more focused modules to improve maintainability.

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

### Active

- [ ] Rate Limiting & Router Safety Net (RES)
- [ ] Chunk State Management (GRP)
- [ ] "True Until Proven Guilty" Grouping Logic (PRMPT)
- [ ] Anti-Hallucination Schema Enforcement (SCHM)

### Out of Scope

- Adding new features or altering existing behavior (pure refactoring).
- Changing the underlying runtime or infrastructure.

## Current Milestone: v2.0 Logic-Based Modular Refactoring

**Goal:** Overhaul the `src` directory structure into a logical, modular monolith. Remove legacy anchor-based tenant discovery and replace it with YAML-driven tenant configuration, ensuring all existing correct functionality is preserved.

**Target features:**
- Modular restructuring (`core`, `utils`, `tenant_config`, `grouping`, `timeline`, `routing`) (ARCH)
- YAML loading and tenant name extraction (YAML)
- Replace anchor logic with YAML-based LLM Name Matching in Pass 1 (PIPE)

## Context

- ✅ Shipped v1.0.
- ✅ Shipped v1.1.
- ✅ Shipped v1.2.
- ✅ Shipped v1.3.
- ✅ Phase 19.1.1.1 complete — updated yaml_loader.py to check `.source_files/` directory.
- The codebase has been successfully cleaned of legacy code and refactored into a modular, maintainable structure.
- All processing logic is now decomposed into single-responsibility modules in `src/cleaning/` and `src/processing/`.
- Error handling is standardized via a custom exception hierarchy in `src/core/exceptions.py`.
- LLM resilience improved using `tenacity` for exponential backoff.
- The system now has a unified, hierarchical logging infrastructure with structured JSONL telemetry for LLM decisions.

## Constraints

- **Functional Parity**: The refactoring must not break existing functionality or change the output format.
- **Maintainability**: The new modules should have clear, single responsibilities.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Break bloated code into new modules | Improves maintainability and file sizes over keeping them in the same file. | ✓ Completed (Phases 2, 3). Codebase is modular. |
| Trace imports from entry point | Safest way to identify truly unused legacy code without false positives. | ✓ Completed (Phase 1). Legacy and unused code removed. |
| Use dual-format logging | balances human readability in app.log with machine-searchability in debug.log. | ✓ Completed (Phase 4). |

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-07-17 completed Phase 19.1.1.1*
