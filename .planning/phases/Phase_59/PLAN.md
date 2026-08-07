# Phase 59: _report.json Paradigm Shift

## Objective
Update the pipeline to hide the raw LLM extraction as `.raw_dump.json` (or similarly named) and explicitly generate a brand new `_report.json` at the end of the Generation Pass that perfectly mirrors the `[Timeline View]`.

## Steps
1. **`src/categorization/categorization.py`**:
   - Change the categorization saving step so it writes to `.raw_dump.json` instead of `_report.json`.

2. **`src/pipeline/runner.py` (and related pipeline codes)**:
   - When proceeding to grouping, it should read from `.raw_dump.json` instead of `_report.json`.
   - Update `state_runner.py` and potentially `main.py` if they reference `_report.json` as the output of categorization.

3. **Generation Pass (`src/reconcile/core.py` and `watcher/orchestrator.py` or similar)**:
   - In both `create` and `append` pathways, after the timeline is built, we need to generate `_report.json`.
   - This `_report.json` should be an array of Grouped Documents containing their assigned `date`, `folder_path`, and `vault_id`.
   - The sequence must match the `[Timeline View]` (001, 002...).

4. **Testing**:
   - Update test mocks/fixtures that simulate `_report.json` as categorization output to use `.raw_dump.json`.
   - Test that `_report.json` is generated successfully at the end of the pipeline with the correct shape.

5. **Documentation**:
   - Update `ROADMAP.md` and `STATE.md`.
   - Produce `SUMMARY.md`.
