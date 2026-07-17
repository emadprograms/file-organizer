# Requirements: v2.0 Logic-Based Modular Refactoring

## Objective
Refactor the `src/` directory into a clean, logic-based modular monolith. The existing functionality is perfect and must be preserved. The "anchor/primary tenant discovery" logic will be retained as a fallback, but the primary method will be reading tenant names directly from a YAML configuration file for future-proofing.

## Constraints
- **Preserve Existing Logic**: Do NOT rewrite or delete functional logic (like PDF parsing, dating, routing). Move existing files/functions into their correct semantic folders.
- **Retain Anchor Logic**: The old logic for discovering primary tenants via anchors should be kept as a fallback mechanism if the YAML configuration is not present.
- **Backward Compatibility**: The final end-to-end output must remain exactly the same.

## Epic: Architecture Restructuring (ARCH)
- [ ] **ARCH-01**: Reorganize `src/` into explicit folders: `core/`, `utils/`, `tenant_config/`, `grouping/`, `timeline/`, `routing/`.
- [ ] **ARCH-02**: Migrate all existing files into their new appropriate locations.

## Epic: YAML Integration (YAML)
- [ ] **YAML-01**: Create `tenant_config/yaml_reader.py` to check the root folder for a "source files" directory and read the YAML configuration.
- [ ] **YAML-02**: Throw a clear error if the YAML file is not found.
- [ ] **YAML-03**: Extract the tenant names from the YAML.

## Epic: Pipeline Integration (PIPE)
- [ ] **PIPE-01**: Retain the old "anchor" logic to act as a fallback for finding primary tenants when the YAML file is not provided.
- [ ] **PIPE-02**: Update Pass 1 of the LLM pipeline (`grouping/name_matcher.py`) to accept the tenant names from the YAML and ask: "Is this name similar to any of the names here?"
- [ ] **PIPE-03**: Update the main orchestrator (`pipeline.py`) to connect the new YAML step to the rest of the pipeline.
