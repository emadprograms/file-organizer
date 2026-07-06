# Discussion Log: Phase 15 - Prune `src/core`

**Date:** 2026-07-06
**Phase:** 15
**Status:** Context Captured

## Discussion Summary

### Area: Dependency Audit for `UserConfig`
- **Questions:** Are there remaining references to `UserConfig` or `Config*` schemas in the test suite?
- **Decision:** Confirmed references exist in `tests/test_organizer.py` and `tests/test_pipeline_extended.py`. Decision made to remove definitions from `src/core` now; test cleanup is deferred to Phase 16.

### Area: `config.py` Import Pruning
- **Questions:** Should we strip `yaml` and `json` imports from `src/core/config.py`?
- **Decision:** Yes. Once `load_user_config` is removed, these imports are obsolete.

### Area: Pipeline Final Prune
- **Observation:** `src/processing/pipeline.py` still contains imports and initialization for `PdfIngestor`, `VisionExtractor`, and `CloudExtractor`.
- **Decision:** These will be removed as part of this phase to ensure a clean codebase.

## Deferred Ideas
- None.
