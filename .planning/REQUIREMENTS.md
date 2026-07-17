# Requirements: v2.0 Logic-Based Modular Refactoring

## Objective
Refactor the `src/` directory into a clean, logic-based modular monolith. The existing functionality is perfect and must be preserved. The "anchor/primary tenant discovery" logic will be retained as a fallback, but the primary method will be reading tenant names directly from a YAML configuration file for future-proofing.

## Constraints
- **Preserve Existing Logic**: Do NOT rewrite or delete functional logic (like PDF parsing, dating, routing). Move existing files/functions into their correct semantic folders.
- **Retain Anchor Logic**: The old logic for discovering primary tenants via anchors should be kept as a fallback mechanism if the YAML configuration is not present.
- **Backward Compatibility**: The final end-to-end output must remain exactly the same.
- **Test Coverage**: All pipeline behaviors — including YAML loading, routing, dry-run, fallback, exception handling, and edge cases (empty tenants, file collisions) — must be comprehensively covered by structured unit tests.

## Epic: Test Suite Quality (TEST)
- [x] **TEST-01**: All test files in `tests/` must be proper `pytest` modules with descriptive names following a strict `test_{module}_{what_is_tested}.py` convention (e.g. `test_utils_telemetry_audit.py`). All old test files must be renamed or converted appropriately.
- [x] **TEST-02**: The `tests/fixtures/golden_1273/` fixture must have a clear `input/` folder (containing the `1273` house directory with `.source_files/` inside it) and an `expected_output/` folder (the exact expected final directory and file structure).
- [x] **TEST-03**: `.source_files/` must be placed exactly inside the target house directory (`golden_1273/input/1273/.source_files/`) so the YAML loader path resolves correctly — matching production behavior.
- [x] **TEST-04**: Intermediate pipeline state files (`1273_cleaned.json`, `1273_grouped.json`, `1273_3_routed_and_finalized.json`) must exist in the golden fixture so dry-run E2E tests can load pre-computed state without calling the LLM.
- [x] **TEST-05**: LLM calls (`canonicalize_with_llm`, `route_document`, etc.) must be mocked at the function level using saved real responses. Responses are captured once by running the pipeline with logging, then saved in fixtures and used as mocks in all E2E tests.
- [x] **TEST-06**: After splitting and routing, tests must assert exactly which files land in which final folder paths (E2E routing destination validation).
- [x] **TEST-07**: Multi-page continuity grouping must use a dedicated, standardized `continuity_test_state.json` array-of-objects fixture to verify the pipeline correctly groups continuous stories and respects hard-reset rules.

## Epic: Architecture Restructuring (ARCH)
- [x] **ARCH-01**: Reorganize `src/` into explicit folders: `core/`, `utils/`, `tenant_config/`, `grouping/`, `timeline/`, `routing/`, `llm/`, `pipeline/`, `pdf/`, `processing/`.
- [x] **ARCH-02**: Migrate all existing files into their new appropriate locations.

## Epic: PDF Processing Enhancements (PDF)
- [x] **PDF-01**: Implement robust PDF compression in `src/pdf/compress.py`. Embedded images must be checked during PDF processing; any image exceeding a maximum dimension of 1500px must be shrunk and compressed using `Pillow` and PyMuPDF to dramatically reduce output file sizes.
- [x] **PDF-02**: Compression logic must gracefully fall back to simple file copying if image parsing fails or if the output size does not successfully reduce.

## Epic: YAML Integration (YAML)
- [x] **YAML-01**: Create `tenant_config/yaml_reader.py` to check the root folder for a "source files" directory and read the YAML configuration.
- [x] **YAML-03**: Extract the tenant names from the YAML.

## Epic: Pipeline Integration (PIPE)
- [x] **PIPE-01**: Retain the old "anchor" logic to act as a fallback for finding primary tenants when the YAML file is not provided.
- [x] **PIPE-02**: Update Pass 1 of the LLM pipeline (`grouping/name_matcher.py`) to accept the tenant names from the YAML and ask: "Is this name similar to any of the names here?"
- [x] **PIPE-03**: Update the main orchestrator (`pipeline.py`) to connect the new YAML step to the rest of the pipeline.
