# Phase 15 Context: Prune `src/core`

## Goal
Remove all legacy YAML-based configuration parsing and associated Pydantic schemas from the `src/core` module to finalize the transition to a hardcoded post-processing architecture.

## Domain
Cleanup of internal configuration and schema logic.

## Decisions

### 1. `src/core/config.py` Cleanup
- Remove `load_user_config` function and `InvalidConfigError` exception.
- Strip unused imports: `yaml` and `json`.
- Retain `AppConfig` and API quota tracking logic as they are still required for the LLM client.

### 2. `src/core/schemas.py` Cleanup
- Delete the following legacy configuration schemas:
    - `ConfigCategory`
    - `ConfigField`
    - `ConfigExtraction`
    - `ConfigGrouping`
    - `ConfigRouting`
    - `ConfigCleaning`
    - `UserConfig`
- Retain `DocumentGroup`, `GroupEntry`, `GroupingResponse`, and other LLM-interaction schemas.

### 3. `src/processing/pipeline.py` Final Prune
- Remove unused imports: `PdfIngestor`, `VisionExtractor`, `CloudExtractor`.
- Remove `self.ingestor = PdfIngestor()` from `Pipeline.__init__`.
- (Note: This closes a gap from Phase 14 where these references were missed).

### 4. Impact on Tests
- Deleting these schemas will cause failures in `tests/test_organizer.py` and `tests/test_pipeline_extended.py`.
- These failures are expected and will be resolved in **Phase 16 (Test Suite Cleanup)**.

## Canonical Refs
- .planning/PROJECT.md
- .planning/REQUIREMENTS.md (specifically CLN-03, CLN-04)

## Code Context
- `src/core/config.py` -> contains the config loading logic to be removed.
- `src/core/schemas.py` -> contains the Pydantic models to be deleted.
- `src/processing/pipeline.py` -> contains the final vestigial imports of the ingestor/extractors.

## Success Criteria
- `src/core/config.py` no longer imports `yaml` or `json` and has no `load_user_config`.
- `src/core/schemas.py` is stripped of all `Config*` and `UserConfig` classes.
- `src/processing/pipeline.py` no longer references `PdfIngestor`, `VisionExtractor`, or `CloudExtractor`.
- The application starts and runs the core pipeline without errors.
