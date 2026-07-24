# Phase 25: Extract Presentation Logic from `core/` - Context

**Gathered:** 2026-07-24T13:20:00+03:00  
**Status:** Ready for planning

<domain>
## Phase Boundary

Extract `src/core/ui.py` to `src/presentation/ui.py`. Move all verbosity control, Rich console instance, and `vprint` logic out of `src/core/` into `src/presentation/`. Update all references and tests.
</domain>

<decisions>
## Implementation Decisions

### D-01: Target File Placement
- `src/core/ui.py` will be moved to `src/presentation/ui.py`.
- `src/presentation/__init__.py` will be created if not present.

### D-02: Public API Preservation
- `src/presentation/ui.py` will export the exact same symbols: `console`, `_verbose`, `set_verbosity`, `vprint`.
- Function signatures and behavior remain completely unchanged.

### D-03: Test Renaming and Logger Test Updates
- `tests/test_core_ui.py` will be moved/renamed to `tests/test_presentation_ui.py`.
- `tests/test_utils_logger.py` module list check will be updated from `"src.core.ui"` to `"src.presentation.ui"`.

### D-04: Documentation Updates
- `architecture_and_directory_map.md` will be updated to reflect `src/presentation/ui.py`.
</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md` — ARCH-01 requirements and acceptance criteria
- `.planning/ROADMAP.md` — Phase 25 overview
- `.planning/STATE.md` — Current milestone and phase status
</canonical_refs>

<code_context>
## Code Context

### Files to relocate/create:
- `src/core/ui.py` -> remove after moving to `src/presentation/ui.py`
- `src/presentation/__init__.py`
- `tests/test_core_ui.py` -> rename to `tests/test_presentation_ui.py`

### Import update sites:
- `src/main.py`
- `src/pipeline/visualizer.py`
- `src/timeline/core.py`
- `src/timeline/reconciliation.py`
- `tests/test_pipeline_visualizer.py`
- `tests/test_utils_logger.py`
</code_context>

---

*Phase: 25-extract-presentation-from-core*  
*Context gathered: 2026-07-24T13:20:00+03:00*
