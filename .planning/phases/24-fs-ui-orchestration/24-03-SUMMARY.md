# Phase 24 Plan 03 Summary

## Actions Taken
- Updated `src/main.py`'s `run_generation_pass` to prevent deletion of `_finalized.pdf` and `_raw_append.pdf`.
- Updated `src/main.py`'s `run_generation_pass` to keep `.source_files` inside `house_dir` for append mode safely.
- Refactored `src/fs_ui/orchestrator.py`'s `finalize()` to replace manual state merging with standard pipeline passes.
- Maintained a `_raw_append.pdf` in `.source_files/` which acts as the source for the pipeline append pass.
- Cleaned up routing checkpoint state so pass 3 is forced to rebuild TOC across the full timeline.

## Results
- Append mode no longer skips grouping/routing passes.
- Re-run pipeline creates correct `.source_files` paths and correctly merges pages into final grouped documents.
