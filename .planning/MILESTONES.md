# Milestones

## v2.0 Logic-Based Modular Refactoring (Shipped: 2026-07-17)

**Phases completed:** 20 phases, 28 plans, 14 tasks

**Key accomplishments:**

- PASSED
- Final validation of Arabic folder routing across all integration tests and E2E flow.
- Overhauled test suite by standardizing naming, structuring deterministic golden fixtures, and isolating E2E tests using function-level mocking.
- Refactored tenant matching and timeline building logic into dedicated modules to align with Phase 16 architecture
- Refactored tenant matching and timeline building logic into dedicated modules to align with Phase 16 architecture
- Updated YAML loader to check the `.source_files/` directory for `{house_id}_tenants.yaml` configuration.

---

## v1.3 Routing Decoupling & Checkpointing (Shipped: 2026-07-10)

**Phases completed:** 3 phases, 3 plans

**Key accomplishments:**

- **Arabic Folder Mapping**: Implemented strict 1:1 mapping of categories to Arabic folder names.
- **System-Wide Renaming**: Migrated all destination folder paths from English to Arabic across the codebase.
- **Pipeline Decoupling**: Refactored `src/processing/pipeline.py` to separate the routing process into its own loop.
- **Granular Checkpointing**: Implemented `RoutingStateManager` to save state atomically.
- **Dynamic Model Configuration**: Updated the routing API to support independent LLM model selection.

---

## v1.2 Pipeline Resilience & Grouping Overhaul (Shipped: 2026-07-10)

**Phases completed:** 5 phases, 13 plans, 0 tasks

**Key accomplishments:**

- PASSED
- Final validation of Arabic folder routing across all integration tests and E2E flow.

---

## v1.0 MVP (Shipped: 2026-07-08)

**Phases completed:** 3 phases, 7 plans, 3 tasks

**Key accomplishments:**

- Removed all unused legacy code from src and updated tests, resulting in a cleaner dependency graph and 100% passing test suite.

---
## v1.1 Logging Overhaul (Shipped: 2026-07-08)

**Phases completed:** 6 phases

**Key accomplishments:**

- **Architectural Refactoring**: Converted monolithic `src/cleaning.py` and `src/processing/` files into modular sub-packages with clean facade exports.
- **Logging Infrastructure**: Implemented a `LogContext` singleton and dual-logging system (human-readable `app.log` and JSONL `debug.log`).
- **Global Migration**: Migrated the entire codebase to a hierarchical logger pattern, replacing all `print` statements with structured logging.
- **LLM Telemetry**: Integrated LLM request/response tracing into the centralized JSONL telemetry system.
- **Validation & Audit**: Completed a full structural and functional audit, ensuring 100% compliance with logging and refactoring standards.
