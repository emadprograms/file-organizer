# Phase 1: Legacy Code Cleanup - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the removal of all unreachable legacy code within the `src/` folder by tracing imports from the main entry point (`src/organize.py`).

</domain>

<decisions>
## Implementation Decisions

### Detection Method
- **D-01:** Use a hybrid approach of static analysis (`vulture` + `grep`) and manual import tracing.
- **D-02:** Manual tracing MUST be handled via isolated sub-agents to prevent context window bloat and ensure the agent does not lose track of the reachability graph.

### Definition of "Unused"
- **D-03:** Strictly unreachable code within the `src/` folder is considered unused. If it is not reachable from `src/organize.py`, it will be removed.
- **D-04:** The `tests/` folder is explicitly ignored for this phase.

### Retention Policy
- **D-05:** Permanent deletion of identified unused code. No archiving.

### Validation Strategy
- **D-06:** Validation requires both the successful execution of the full existing `tests/` suite and a mandatory end-to-end smoke test on a real PDF to ensure the core workflow is 100% maintained.

### Claude's Discretion
- **Toolchain:** Claude has chosen a `vulture` + `grep` toolchain for the static analysis portion of the hybrid approach to maintain transparency and speed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Foundation
- `.planning/PROJECT.md` — High-level project goals and value proposition.
- `.planning/REQUIREMENTS.md` — Detailed requirements for the cleanup and refactoring.
- `.planning/STATE.md` — Current project state and phase progress.

### Codebase Analysis
- `.planning/codebase/STRUCTURE.md` — Detailed directory layout and component purposes.
- `.planning/codebase/ARCHITECTURE.md` — System overview, data flow, and architectural constraints.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/organize.py`: The primary entry point from which all reachability must be traced.

### Established Patterns
- **Sequential Pipeline:** The application follows a cleaning $ightarrow$ grouping $ightarrow$ routing flow. Any code not contributing to this pipeline is targeted.

### Integration Points
- All `src/` files that are imported by `src/organize.py` (directly or indirectly) are the "safe" zone.

</code_context>

<specifics>
## Specific Ideas

- The user has emphasized that maintaining the current workflow is **paramount**.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Legacy Code Cleanup*
*Context gathered: 2026-07-07*
