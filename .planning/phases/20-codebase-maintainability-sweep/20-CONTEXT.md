# Phase 20: Codebase Maintainability Sweep - Context

**Gathered:** 2026-07-18T13:12:05+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

Adding complete Python type hints and clear docstrings to all v2.0 modules (`core`, `utils`, `grouping`, `routing`, etc.) to improve codebase maintainability.

</domain>

<decisions>
## Implementation Decisions

### Type Checking Validation
- **D-01:** Add hints for IDE autocomplete only. Do not set up strict type checkers (mypy/pyright) to avoid configuration rabbit holes and keep the sweep focused.

### Typing Style Consistency
- **D-02:** Enforce modern Python 3.9+ built-in generics (e.g., `list[str]`, `dict[str, Any]`) across all v2.0 modules, migrating away from `typing.List` / `typing.Dict`.

### Private Method Docstrings
- **D-03:** Write docstrings for *every single function and class*, including complex internal private methods (e.g., `_route_llm_call`), strictly fulfilling the updated MAINT-01 requirement.

### Test Files Scope
- **D-04:** Extend the type-hinting and docstring sweep to both `src/` and `tests/` directories to maximize maintainability.

### the agent's Discretion
None — user made explicit choices for all areas.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture and Requirements
- `.planning/codebase/CONVENTIONS.md` — Defines Google-style docstrings and Python 3 built-in typing conventions.
- `.planning/PROJECT.md` — Hybrid architecture decision (Functional pipeline, OOP FS-UI).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/core/schemas.py`: Existing Pydantic models will need accurate type hints and docstrings.

### Established Patterns
- Functional data pipeline: The v2.0 refactor established a functional pipeline (`cleaning.py`, `processing/pipeline.py`) which must be preserved. Future FS-UI listeners (Phases 22-24) will use classes, but this phase (Phase 20) only annotates the existing functional code.

### Integration Points
- `tests/` directory: Must be type-hinted and documented along with `src/`.

</code_context>

<specifics>
## Specific Ideas

- The user specifically requested modifying `MAINT-01` to require docstrings for "every single function" rather than just public interfaces.
- The user clarified that the current functional implementation should remain as-is for the document pipeline, while future append-mode/FS-UI listeners will use class-based orchestrators.

</specifics>

<deferred>
## Deferred Ideas

- Introducing class-based orchestrators (deferred to Phase 22-24 for the FS-UI listener).

</deferred>

---

*Phase: 20-Codebase Maintainability Sweep*
*Context gathered: 2026-07-18T13:12:05+03:00*
