# Milestone v2.0 — Project Summary

**Generated:** 2026-07-16
**Purpose:** Team onboarding and project review

---

## 1. Project Overview

A technical debt cleanup and refactoring effort for the file organizer project. The goal is to remove unused legacy code by tracing imports from the main entry point, and to break down bloated functions and files into smaller, more focused modules to improve maintainability.

The **v2.0 Logic-Based Modular Refactoring** milestone specifically overhauls the `src` directory structure into a logical, modular monolith. It removes legacy anchor-based tenant discovery and replaces it with YAML-driven tenant configuration (`tenants.yaml`), ensuring all existing correct functionality is preserved.

## 2. Architecture & Technical Decisions

- **Decision:** Reorganize `src/` into logical folders (`core/`, `utils/`, `tenant_config/`, `grouping/`, `timeline/`, `routing/`).
  - **Why:** To improve maintainability and decouple subsystems.
  - **Phase:** 16
- **Decision:** Introduce a YAML-based configuration (`tenants.yaml`) allowing users to explicitly override tenant timeline generation.
  - **Why:** To replace rigid anchor-based discovery logic with a future-proof, user-editable configuration.
  - **Phase:** 17 & 18
- **Decision:** Implement a dual-mode YAML execution strategy.
  - **Why:** If `tenants.yaml` is missing, the system uses anchor logic as a fallback and automatically generates the YAML file with discovered tenants. If it exists, it restricts parsing strictly to the YAML values.
  - **Phase:** 18
- **Decision:** Move checkpoint system (`.run_cache`) and `_report.json` into a hidden `.source_files/` directory.
  - **Why:** To clean up the root output directory and encapsulate intermediate files.
  - **Phase:** 18
- **Decision:** Keep `*_categorized.pdf` and `tenants.yaml` in the root target directory.
  - **Why:** For easier manual user access.
  - **Phase:** 18

## 3. Phases Delivered

| Phase | Name | Status | One-Liner |
|-------|------|--------|-----------|
| 16 | Setup New Directory Structure | Complete | Reorganize `src/` into logical folders preserving functionality. |
| 16.1 | Cleanup Checkpoints System | Complete | Refactor confusing checkpoint system into `.source_files/`. |
| 17 | Implement YAML Configuration Loading | Complete | Create YAML parser and validation for `tenants.yaml`. |
| 18 | Refactor Pipeline to use YAML | Complete | Remove anchor logic and integrate YAML into Pass 1 of the pipeline. |
| 18.5 | Finalize PDF Output, Compression, and Metadata | Complete | Ensure correct output naming, PDF metadata, and standard compression. |
| 18.6 | Fix Fallback Model Behavior Across Codebase | Complete | Standardize failover logic for LLMs across the application. |
| 19 | End-to-End Testing and Verification | Complete | Verify exact end-to-end results parity with the new architecture. |

## 4. Requirements Coverage

- ✅ **ARCH-01**: Reorganize `src/` into explicit folders (`core`, `utils`, `tenant_config`, `grouping`, `timeline`, `routing`).
- ✅ **ARCH-02**: Migrate all existing files into their new appropriate locations.
- ✅ **YAML-01**: Create `tenant_config/yaml_loader.py` to check the root folder for a "source files" directory and read the YAML configuration.
- ✅ **YAML-02**: Handle missing YAML with auto-generation fallback.
- ✅ **YAML-03**: Extract the tenant names from the YAML.
- ✅ **PIPE-01**: Remove/bypass the old "anchor" logic used for finding primary tenants when YAML is present.
- ✅ **PIPE-02**: Update Pass 1 of the LLM pipeline to accept the tenant names from the YAML.
- ✅ **PIPE-03**: Update the main orchestrator to connect the new YAML step to the rest of the pipeline.

## 5. Key Decisions Log

- **D-01 (Ph 17):** The `tenants.yaml` file will contain a simple list of strings.
- **D-02 (Ph 17):** The configuration will be loaded from a file specifically named `tenants.yaml` located in the root output directory.
- **D-03 (Ph 17):** Pydantic schema model validation will be used to strictly validate the loaded YAML data.
- **D-06 (Ph 18):** Initial Discovery (No YAML): Pass 1 runs the current strict Anchor Logic. After extracting timelines, it automatically generates `tenants.yaml` with discovered tenant names.
- **D-07 (Ph 18):** When `tenants.yaml` exists, the LLM is explicitly provided the tenant names from the YAML. It maps any raw OCR names strictly to these known identities.
- **D-10 (Ph 18):** Has Date, No Name: Assign to the tenant whose YAML timeline covers the document's date. If overlapping, assign to the newest tenant.
- **D-11 (Ph 18):** No Date, No Name: Assign to the latest tenant overall.

## 6. Tech Debt & Deferred Items

- Test paths for fixtures and assertions were migrated to target the new `.source_files/` directory instead of `.run_cache`.
- `1273_report.json` was added to `tests/fixtures/golden_1273/` bypassing `.gitignore` for manual `dry-run` validations.
- Updated `test_organizer.py` assertions to align with the RTL-safe date formatting `\u200E(YYYY - YYYY)\u200E` as designed during localization fixes.

## 7. Getting Started

- **Run the project:** `python src/main.py [pdf_path]` (use `--dry-run` for safe validation)
- **Key directories:** `src/core/`, `src/utils/`, `src/tenant_config/`, `src/grouping/`, `src/timeline/`, `src/routing/`
- **Tests:** `pytest tests/` (179 tests ensuring total pipeline stability)
- **Where to look first:** `src/main.py` is the entry point that orchestrates `src/timeline/core.py` and `src/pipeline/pipeline.py`.

---

## Stats

- **Timeline:** 2026-07-10 → 2026-07-16 (v2.0 execution)
- **Phases:** 7 / 7 complete
- **Commits:** 34
- **Files changed:** 126 (+2853 / -1389)
- **Contributors:** Emad Arshad Alam
