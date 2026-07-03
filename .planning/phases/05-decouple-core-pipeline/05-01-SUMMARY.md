# 05-decouple-core-pipeline - 01

## Execution Summary
- **Phase:** 05-decouple-core-pipeline
- **Plan:** 01-PLAN.md
- **Status:** Completed

## Tasks Completed
- Task 1: Decouple schemas and LLM from domain logic
- Task 2: Implement pipeline orchestration and fallback
- Task 3: Implement organizer externalization and declarative routing

## Changes Made
- `src/schemas.py`: Removed hardcoded `Category` Enum and `PageClassification`. Updated `ConfigRouting` to use `rules` dict.
- `src/llm.py`: Removed domain-specific `_build_system_prompt`. Added `prompt_template` argument to `cluster_names`, `detect_date_outliers`, `check_bulk_semantic_grouping`.
- `src/pipeline.py`: Replaced `PageClassification` with dynamic `PageData`. Updated pass 2 grouping to dynamically load python script if specified, with a fallback to declarative grouping.
- `src/organizer.py`: Removed legacy helper methods and `CATEGORY_FOLDERS`. Rewrote `organize()` to dynamically load python script, with fallback to declarative dictionary-based routing (`config.routing.rules`).

## Follow-up / Next Steps
- Verify the system with unit tests or integration tests.
- Update `test_cache.json` or config loading to match the new `ConfigRouting` schema where `destination_format` is replaced by `rules`.
