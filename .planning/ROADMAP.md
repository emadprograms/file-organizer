# Milestone v3.0 Roadmap

**5 phases** | **12 requirements mapped** | All covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 20 | Codebase Maintainability Sweep | Add type hinting and docstrings to v2.0 modules | MAINT-01 | 1 |
| 21 | System Unification (Categorization) | Port file-categorizer logic for `_report.json` generation | CAT-01, CAT-02 | 2 |
| 22 | Configuration & CLI Modes | Create config.yaml and setup explicit CLI commands | CONF-01, CONF-02, CONF-03 | 3 |
| 23 | Inbox Parsing & Syntax | Build parser for space-separated FS-UI commands | FSUI-01, FSUI-02, FSUI-03 | 3 |
| 24 | FS-UI Orchestration (Append Mode) | Wire up the rename loop and finalize filing logic | FSUI-04, FSUI-05 | 3 |

### Phase Details

**Phase 20: Codebase Maintainability Sweep**
Goal: Add type hinting and docstrings to v2.0 modules
Requirements: MAINT-01
Success criteria:
1. All modules in `src/core`, `src/utils`, `src/grouping`, etc. have Python type hints and docstrings.

**Phase 21: System Unification (Categorization)**
Goal: Port file-categorizer logic for `_report.json` generation
Requirements: CAT-01, CAT-02
Success criteria:
1. `src/categorization/` module can run OCR and call Gemini 3.1 Flash Lite to generate `_report.json`.
2. Pipeline skips OCR/LLM if `_report.json` already exists.

**Phase 22: Configuration & CLI Modes**
Goal: Create config.yaml and setup explicit CLI commands
Requirements: CONF-01, CONF-02, CONF-03
Success criteria:
1. `config.yaml` loads `inbox_path` and `area_mappings`.
2. `main.py create <path>` triggers history-building.
3. `main.py append` triggers Inbox watcher.

**Phase 23: Inbox Parsing & Syntax**
Goal: Build parser for space-separated FS-UI commands
Requirements: FSUI-01, FSUI-02, FSUI-03
Success criteria:
1. Parser correctly extracts `[AREA] [HOUSE] [GROUP] [DATE]` from filenames.
2. Parser detects `U` and flags it for LLM inference.
3. Single-house rule is enforced across the parsed document.

**Phase 24: FS-UI Orchestration (Append Mode)**
Goal: Wire up the rename loop and finalize filing logic
Requirements: FSUI-04, FSUI-05
Success criteria:
1. System successfully renames processed PDFs with `_Proposed`.
2. System detects ` OK` suffix and moves the file to the correct house.
3. `.source_files/` JSON and `_finalized` PDF are updated correctly.
