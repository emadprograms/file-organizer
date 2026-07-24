# Phase 27: Disambiguate Reconciliation Modules - Context

**Gathered:** 2026-07-24T13:26:00+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary
Rename `timeline/reconciliation.py` to `timeline/page_integrity.py` and update associated tests and imports to eliminate ambiguity with the `src/reconcile` module.
</domain>

<decisions>
## Implementation Decisions
- **D-01:** Rename `src/timeline/reconciliation.py` to `src/timeline/page_integrity.py`.
- **D-02:** Rename `tests/test_timeline_reconciliation.py` to `tests/test_timeline_page_integrity.py`.
- **D-03:** Update `src/timeline/__init__.py` and the `@patch` target in the test file.
</decisions>
