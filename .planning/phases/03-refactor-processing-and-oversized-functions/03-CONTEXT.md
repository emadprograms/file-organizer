# Phase 03: Refactor Processing and Oversized Functions - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the refactoring of bloated files in `src/processing/` and oversized functions across the application. It also addresses specific technical debt in `src/llm/llm.py` and `src/processing/split.py` to improve maintainability and reliability.
</domain>

<decisions>
## Implementation Decisions

### Module Breakdown and Directory Structure
- **D-01:** Break bloated files in `src/processing/` into sub-packages (e.g., `src/processing/routing/`) for better isolation rather than keeping a flat structure.

### LLM Layer Refactoring
- **D-02:** Refactor `src/llm/llm.py` to address hardcoded rate limits (by utilizing `tenacity` for backoff) and separate test/mock logic from production routing.

### Exception Handling Strategy
- **D-03:** Implement a custom exception hierarchy (e.g., `FileOrganizerError`, `ConfigurationError`) to replace deep `sys.exit` calls and swallowed exceptions, enabling proper error propagation and logging.

### PDF Compression and Pillow Dependency
- **D-04:** Refactor `src/processing/split.py` to use a PyMuPDF-only compression method, completely eliminating the need for the `Pillow` dependency and the brittle dynamic pip install.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Foundation
- `.planning/PROJECT.md` — High-level project goals, emphasizing that functionality must not break.
- `.planning/REQUIREMENTS.md` — Detailed requirements mapped to this phase (REF-02, REF-03).
- `.planning/STATE.md` — Current project state.

### Codebase Architecture
- `.planning/codebase/STRUCTURE.md` — Defines current file layout.
- `.planning/codebase/ARCHITECTURE.md` — Outlines the pipeline data flow and dependencies.
- `.planning/codebase/CONCERNS.md` — Highlights specific technical debt items (Pillow dependency, LLM rate limits, deep sys.exits) addressed in this phase.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- PyMuPDF (`fitz`): Powerful PDF library already in use, which can handle native image compression without Pillow.
- `tenacity`: Already in `requirements.txt` and should be leveraged in `src/llm/llm.py`.

### Established Patterns
- The application relies on pipeline stages. Refactoring into sub-packages allows defining clean module-level APIs (e.g., `src/processing/routing/__init__.py`) to hide internal complexity.
</code_context>

<specifics>
## Specific Ideas

- The user requested PyMuPDF-only compression to simplify the dependency graph.

</specifics>

<deferred>
## Deferred Ideas

None.
</deferred>

---

*Phase: 03-Refactor Processing and Oversized Functions*
*Context gathered: 2026-07-08*
