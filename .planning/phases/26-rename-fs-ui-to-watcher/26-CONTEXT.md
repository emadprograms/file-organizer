# Phase 26: Rename `fs_ui/` to `watcher/` - Context

**Gathered:** 2026-07-24T13:25:00+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary
Rename `src/fs_ui/` to `src/watcher/`, rename 4 test files, and update all module and mock patch references across the codebase to ensure `pytest` continues to pass.
</domain>

<decisions>
## Implementation Decisions
- **D-01:** Rename `src/fs_ui` to `src/watcher` directly using git mv to preserve history.
- **D-02:** Rename test files mapping `fs_ui` -> `watcher`.
- **D-03:** Use targeted replacements for all `src.fs_ui` import references and `@patch`/`patch()` string literals in the test suite.
</decisions>
