# Phase 02: Refactor src/cleaning.py - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the refactoring of `src/cleaning.py` into a structured, modular package based on responsibility. It breaks down bloated code and oversized functions while preserving exact functional parity.

</domain>

<decisions>
## Implementation Decisions

### Module Breakdown and Directory Structure
- **D-01:** Create a new `src/cleaning/` package to encapsulate all data standardization and tenant resolution logic.
- **D-02:** Separate responsibilities into individual files within the package (e.g., `dates.py`, `tenants.py`, `models.py`).

### Date Parsing Logic
- **D-03:** Keep date parsing strictly encapsulated within the new cleaning package (e.g., `src/cleaning/dates.py`), as its massive heuristic logic is primarily scoped to cleaning. Do not extract to a global core utility.

### API Interface
- **D-04:** Use the Facade pattern. Create an `__init__.py` in `src/cleaning/` that exports a single `process_cleaning_phase` entry point. The main orchestrator (`src/organize.py`) should interact only with this facade, hiding the internal modular complexity.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Foundation
- `.planning/PROJECT.md` — High-level project goals, emphasizing that functionality must not break.
- `.planning/REQUIREMENTS.md` — Detailed requirements mapped to this phase (REF-01).
- `.planning/STATE.md` — Current project state.

### Codebase Architecture
- `.planning/codebase/STRUCTURE.md` — Defines current file layout and where new code should live.
- `.planning/codebase/ARCHITECTURE.md` — Outlines the pipeline data flow (Cleaning -> Grouping -> Routing) and dependencies.
- `.planning/phases/01-legacy-code-cleanup/01-CONTEXT.md` — Phase 1 decisions, noting that core behavior must remain unchanged.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PageData` and `TenantTimeline` models: Can be cleanly migrated to a dedicated `models.py` inside the new `src/cleaning/` package.
- `_ENGLISH_MONTH_MAP`, `_HIJRI_ARABIC_MONTH_MAP`, and `parse_flexible_date`: Logic to be grouped into `dates.py`.
- `cluster_names_fuzzily` and `canonicalize_with_llm`: Tenant logic to be grouped into `tenants.py`.

### Established Patterns
- **LLM Canonicalization:** Uses structured prompts with `LLMClient`. The LLM usage remains identical.
- **Data Models:** Driven by Pydantic models (like `PageData`).

### Integration Points
- `src/organize.py` currently imports `process_cleaning_phase` from `src.cleaning`. This will change to `from src.cleaning import process_cleaning_phase`, facilitated by `__init__.py`.
- `src/processing/pipeline.py` may also depend on the output schema of the cleaning phase.

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond adhering to the Facade pattern.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-Refactor src/cleaning.py*
*Context gathered: 2026-07-07*
