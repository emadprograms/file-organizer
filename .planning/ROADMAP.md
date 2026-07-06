# Milestone v1.1 Roadmap: Legacy Code Cleanup

## Phase 12: Config & Scripts Cleanup
**Goal:** Remove unused YAML configuration files and the legacy scripts directory to declutter the root.
**Requirements:** CLN-01, CLN-02
**Success Criteria:**
1. `config.yaml` and `sample-config.yaml` are deleted.
2. `scripts/` directory is deleted.
3. Codebase tests still pass (or tool execution completes without looking for these files).

## Phase 13: Prune `src/core`
**Goal:** Strip out YAML parsing logic and unused schema classes.
**Requirements:** CLN-03, CLN-04
**Success Criteria:**
1. `load_user_config` and `InvalidConfigError` removed from `src/core/config.py`.
2. `UserConfig`, `ConfigCategory`, `ConfigExtraction`, `ConfigCleaning`, `ConfigGrouping`, `ConfigRouting`, `ConfigField` removed from `src/core/schemas.py`.
3. The remaining types in `schemas.py` (`DocumentGroup` etc.) remain intact.

## Phase 14: Remove Dead Processing Modules
**Goal:** Delete `extractors.py` and `ingest.py` since the tool is now a JSON post-processor and does not extract PDFs via Vision/LLM itself.
**Requirements:** CLN-05, CLN-06
**Success Criteria:**
1. `src/processing/extractors.py` deleted.
2. `src/processing/ingest.py` deleted.

## Phase 15: Pipeline Orchestrator Cleanup
**Goal:** Clean up the legacy pipeline methods in `src/processing/pipeline.py`.
**Requirements:** CLN-07, CLN-08
**Success Criteria:**
1. `process_pdf`, `_run_cleaning_pass`, `_interpolate_dates`, `_map_aliases`, `_parse_date` deleted from `pipeline.py`.
2. `config` parameter removed from `_group_and_route_documents` (and its signature updated in `organize.py` where it's called).
3. The pipeline can successfully be imported and used by `organize.py` without throwing runtime errors.
