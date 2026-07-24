# Phase 29: Audit Test Mock Patch Targets - Context

**Gathered:** 2026-07-24T13:30:00+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary
Audit all `@patch` targets in the test suite to ensure they correctly patch symbols at the import site instead of the definition module, focusing heavily on `main.py` testing left over from the runner extraction.
</domain>

<decisions>
## Implementation Decisions
- **D-01:** Replaced `@patch("src.pipeline.pipeline.Pipeline")` and `@patch("src.timeline.FileOrganizer")` with mock targets for `run_cleaning_pass`, `run_grouping_pass`, `run_routing_pass`, and `run_generation_pass` located at `src.main.*`.
- **D-02:** Updated `test_root_main_cli.py` assertions to check the mock call count for these runner functions instead of checking the `Pipeline` call count.
</decisions>
