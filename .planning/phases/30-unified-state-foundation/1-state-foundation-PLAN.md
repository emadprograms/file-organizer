---
status: implemented
---

# Phase 30: Unified State Foundation

## Context
We are migrating from three separate checkpoint JSONs (1_cleaned, 2_grouped, 3_routed) to a single unified `state.json` per house. This is a purely architectural change to make state atomic and reliable, and to support the Vault architecture coming in Phase 31.

## Requirements
- **STATE-01**: Define `state.json` schema to encompass all previous pipeline states.
- **STATE-02**: Modify `pipeline/runner.py` to read and write a single `state.json`.
- **STATE-03**: Remove creation of `1_cleaned.json`, `2_grouped.json`, and `3_routed_and_finalized.json`.
- **STATE-04**: Maintain crash-safe atomic writes for `state.json`.

## Steps
1. Create `src/core/state.py` with a `State` class that handles loading, saving, and updating document entries. It must use atomic file writes via `tempfile` and `os.replace`.
2. Update `src/pipeline/runner.py`. Instead of reading/writing the three individual checkpoint JSON files, it will initialize the `State` object once.
3. Update `run_cleaning_pass`, `run_grouping_pass`, `run_routing_pass`, and `run_generation_pass` in `runner.py` to mutate and flush `State` instead of independent dictionaries.
4. Remove all legacy code generating `1_cleaned.json`, `2_grouped.json`, and `3_routed_and_finalized.json`.
5. Run the test suite (`pytest`) and update any mock patches in `test_pipeline.py` or other tests that relied on checking the old JSON files. Ensure they now check `state.json`.

