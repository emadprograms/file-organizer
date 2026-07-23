# Requirements

## Milestone v3.0 Requirements

### Codebase Maintainability

- [x] **MAINT-01**: User can verify that all v2.0 modules (`core`, `utils`, `grouping`, `routing`, etc.) have complete Python type hinting and clear docstrings for every single function and class.

### System Unification (Categorization)

- [x] **CAT-01**: System can extract structured metadata (`_report.json`) from a raw PDF document using OCR and Gemini 3.1 Flash Lite.
- [x] **CAT-02**: System can bypass the LLM/OCR extraction step entirely if a `_report.json` file is already present for the document.

### Configuration & CLI Modes

- [x] **CONF-01**: User can configure `inbox_path`, `areas_root_path`, and `area_mappings` within a central `config.yaml` file.
- [x] **CONF-02**: User can launch the script in `create` mode (e.g. `python main.py create <path>`), which forces standard history-building logic only on valid house structures.
- [x] **CONF-03**: User can launch the script in `append` mode (e.g. `python main.py append`), which starts the File-System UI listener on the inbox.

### Inbox Parsing & File-System UI

- [x] **FSUI-01**: System can parse positional filename commands in the format `[AREA_CODE] [HOUSE_NUMBER] [GROUP] [DATE]` separated by spaces.
- [x] **FSUI-02**: System interprets the `U` character in any position as an instruction to dynamically infer that missing data (Area, House, Group, or Date) from the document content using the LLM.
- [x] **FSUI-03**: System assumes any PDF dropped into the inbox belongs to exactly ONE house, and applies majority-vote logic if the house must be inferred.
- [x] **FSUI-04**: System can propose its filing intention by renaming the PDF in the Inbox (appending `_Proposed`), preserving all 6 fields, and running the necessary extraction and pipeline passes (cleaning, grouping, routing) during the propose phase to store intermediate results.
- [x] **FSUI-05**: System watches the Inbox for user approval (indicated by appending ` OK` to the filename) and finalizes by extracting pages to tenant folders, appending pages to the `_finalized` PDF, shifting page indices and merging temporary JSONs into main `.source_files/`, and cleaning up the inbox.
- [x] **FSUI-06**: System aborts append mode and appends `_Error_Missing_YAML.pdf` to the filename if the required `house_id_tenants.yaml` file is missing.

## Future Requirements

(None defined for now)

## Out of Scope

- Splitting a single PDF that contains documents belonging to multiple different houses automatically.
- Database integration (the filesystem is the single source of truth).

## Traceability

| Requirement | Phase | Plan | Verification | Status |
|-------------|-------|------|--------------|--------|
| **MAINT-01** | Phase 20 | 1, 2, 3 | `20-VERIFICATION.md` | Satisfied |
| **CAT-01** | Phase 21 | 21 | `21-VERIFICATION.md` | Satisfied |
| **CAT-02** | Phase 21 | 21 | `21-VERIFICATION.md` | Satisfied |
| **CONF-01** | Phase 22 | 22-01 | `22-VERIFICATION.md` | Satisfied |
| **CONF-02** | Phase 22 | 22-02 | `22-VERIFICATION.md` | Satisfied |
| **CONF-03** | Phase 22 | 22-02 | `22-VERIFICATION.md` | Satisfied |
| **FSUI-01** | Phase 23 | 23-01 | `23-VERIFICATION.md` | Satisfied |
| **FSUI-02** | Phase 23 | 23-02 | `23-VERIFICATION.md` | Satisfied |
| **FSUI-03** | Phase 23 | 23-02 | `23-VERIFICATION.md` | Satisfied |
| **FSUI-04** | Phase 24 | 24-02 | `24-VERIFICATION.md` | Satisfied |
| **FSUI-05** | Phase 24 | 24-02 | `24-VERIFICATION.md` | Satisfied |
| **FSUI-06** | Phase 24 | 24-01 | `24-VERIFICATION.md` | Satisfied |
