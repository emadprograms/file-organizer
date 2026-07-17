# Requirements: v2.0 Logic-Based Modular Refactoring

## Objective
Refactor the `src/` directory into a clean, logic-based modular monolith. The existing functionality is perfect and must be preserved. The "anchor/primary tenant discovery" logic will be retained as a fallback, but the primary method will be reading tenant names directly from a YAML configuration file for future-proofing.

## Constraints
- **Preserve Existing Logic**: Do NOT rewrite or delete functional logic (like PDF parsing, dating, routing). Move existing files/functions into their correct semantic folders.
- **Retain Anchor Logic**: The old logic for discovering primary tenants via anchors should be kept as a fallback mechanism if the YAML configuration is not present.
- **Backward Compatibility**: The final end-to-end output must remain exactly the same.
- **Test Coverage**: All pipeline behaviors — including YAML loading, routing, dry-run, and fallback — must be covered by structured `test_[module].py` tests using function-level LLM mocking with saved responses.

## Epic: Test Suite Quality (TEST)
- [ ] **TEST-01**: All test files in `tests/` must follow the strict `test_[module].py` naming convention AND have names that clearly describe what they test. **Not yet done.** Current violations:
  - `uat_08_*.py` (6 files) — not prefixed with `test_`, not picked up by pytest, completely opaque (e.g. `uat_08_precision_window.py`)
  - `verify_*.py` (12 files) — not prefixed with `test_`, purpose is unclear (e.g. `verify_uat_11_1.py` tells you nothing)
  - `test_phase12_finalization.py`, `test_phase7_features.py`, `test_phase7_uat.py`, `test_uat_09_01.py` etc. — phase numbers in test names are meaningless to anyone reading the suite cold
  - `create_continuity_fixture.py` — a utility script living in the test folder with no clear identity
  - All files must be renamed to `test_[what_it_actually_tests].py` (e.g. `verify_uat_11_1.py` → `test_routing_conditional_llm.py`)
- [ ] **TEST-02**: The `tests/fixtures/golden_1273/` fixture must have a clear `input/` folder (containing the `1273` house directory with `.source_files/` inside it) and an `expected_output/` folder (the exact expected final directory and file structure).
- [ ] **TEST-03**: `.source_files/` must be placed exactly inside the target house directory (`golden_1273/input/1273/.source_files/`) so the YAML loader path resolves correctly — matching production behavior.
- [ ] **TEST-04**: Intermediate pipeline state files (`1273_cleaned.json`, `1273_grouped.json`, `1273_3_routed_and_finalized.json`) must exist in the golden fixture so dry-run E2E tests can load pre-computed state without calling the LLM.
- [ ] **TEST-05**: LLM calls (`canonicalize_with_llm`, `route_document`, etc.) must be mocked at the function level using saved real responses. Responses are captured once by running the pipeline with logging, then saved in fixtures and used as mocks in all E2E tests.
- [ ] **TEST-06**: After splitting and routing, tests must assert exactly which files land in which final folder paths (E2E routing destination validation).

## Epic: Architecture Restructuring (ARCH)
- [x] **ARCH-01**: Reorganize `src/` into explicit folders: `core/`, `utils/`, `tenant_config/`, `grouping/`, `timeline/`, `routing/`.
- [x] **ARCH-02**: Migrate all existing files into their new appropriate locations.

## Epic: YAML Integration (YAML)
- [x] **YAML-01**: Create `tenant_config/yaml_reader.py` to check the root folder for a "source files" directory and read the YAML configuration.

- [x] **YAML-03**: Extract the tenant names from the YAML.

## Epic: Pipeline Integration (PIPE)
- [x] **PIPE-01**: Retain the old "anchor" logic to act as a fallback for finding primary tenants when the YAML file is not provided.
- [x] **PIPE-02**: Update Pass 1 of the LLM pipeline (`grouping/name_matcher.py`) to accept the tenant names from the YAML and ask: "Is this name similar to any of the names here?"
- [x] **PIPE-03**: Update the main orchestrator (`pipeline.py`) to connect the new YAML step to the rest of the pipeline.
