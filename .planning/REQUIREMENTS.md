# Requirements

## Milestone v3.0 Requirements

### Codebase Maintainability

- [x] **MAINT-01**: User can verify that all v2.0 modules (`core`, `utils`, `grouping`, `routing`, etc.) have complete Python type hinting and clear docstrings for every single function and class.

### System Unification (Categorization)

- [x] **CAT-01**: System can extract structured metadata (`_report.json`) from a raw PDF document using OCR and Gemini 3.1 Flash Lite.
- [x] **CAT-02**: System can bypass the LLM/OCR extraction step entirely if a `_report.json` file is already present for the document.

### Configuration & CLI Modes

- [ ] **CONF-01**: User can configure `inbox_path`, `areas_root_path`, and `area_mappings` within a central `config.yaml` file.
- [ ] **CONF-02**: User can launch the script in `create` mode (e.g. `python main.py create <path>`), which forces standard history-building logic only on valid house structures.
- [ ] **CONF-03**: User can launch the script in `append` mode (e.g. `python main.py append`), which starts the File-System UI listener on the inbox.

### Inbox Parsing & File-System UI

- [ ] **FSUI-01**: System can parse positional filename commands in the format `[AREA_CODE] [HOUSE_NUMBER] [GROUP] [DATE]` separated by spaces.
- [ ] **FSUI-02**: System interprets the `U` character in any position as an instruction to dynamically infer that missing data (Area, House, Group, or Date) from the document content using the LLM.
- [ ] **FSUI-03**: System assumes any PDF dropped into the inbox belongs to exactly ONE house, and applies majority-vote logic if the house must be inferred.
- [ ] **FSUI-04**: System can propose its filing intention by renaming the PDF in the Inbox (e.g. appending `_Proposed`).
- [ ] **FSUI-05**: System watches the Inbox for user approval (indicated by appending ` OK` to the filename) and finalizes the filing process (moving the file to the correct house's `.source_files/` and updating the `_finalized` PDF) upon detection.
- [x] **FSUI-06**: FS-UI listener and orchestration is implemented using a class-based architecture to encapsulate state, keeping it strictly separated from the functional document pipeline.

## Future Requirements

(None defined for now)

## Out of Scope

- Splitting a single PDF that contains documents belonging to multiple different houses automatically.
- Database integration (the filesystem is the single source of truth).

## Traceability

(Will be filled by the roadmap)
