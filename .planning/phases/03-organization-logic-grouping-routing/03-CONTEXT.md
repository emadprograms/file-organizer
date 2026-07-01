# Phase 3: Organization Logic (Grouping & Routing) - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the generalization of Pass 2 (grouping contiguous pages into documents) and Pass 3 (routing documents into folders) to use constraints and paths defined entirely by the user-provided configuration, replacing hardcoded rules.

</domain>

<decisions>
## Implementation Decisions

### Grouping Boundaries (Pass 2)
- **D-01:** Hybrid approach: Provide both simple declarative `group_by` fields in the config (e.g. `[category, resident]`) and an optional Python script for complex boundary logic (like recreating the semantic LLM splitting).

### Routing Strategy (Pass 3)
- **D-02:** Hybrid approach: Use simple template strings for paths (e.g. `./output/{resident}/{date}_{category}.pdf`) and an optional Python script for edge cases with complex conditional logic.

### Orphan/Unknown Handling
- **D-03:** The user defines a `fallback_folder` path in the config for all unmatched or unclassified documents.

### the agent's Discretion
Any details regarding the exact schema definitions for these grouping/routing configurations in the Pydantic models.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specifications
- `.planning/REQUIREMENTS.md` — Defines requirements for grouping and organization (GRP-01, ORG-01).
- `.planning/ROADMAP.md` — Defines phase 3 goals and success criteria.

### Architecture and Structure
- `.planning/codebase/ARCHITECTURE.md` — Overview of pipeline architecture that we must maintain.
- `.planning/codebase/STRUCTURE.md` — Directory structure rules.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/schemas.py`: Where the new grouping and routing configuration models should be housed.
- `src/pipeline.py`: Where `_group_pages_into_documents` resides and must be updated.
- `src/organizer.py`: Where the logic for resolving directory paths and copying documents resides.

### Established Patterns
- Pydantic models for configuration validation.
- Dynamic python script importing (established in Pass 1.5 `_run_cleaning_pass` in `src/pipeline.py`).

### Integration Points
- `src/pipeline.py` (Pass 2): Will ingest the new `config.grouping` settings to replace hardcoded tuple checks and the hardcoded LLM call.
- `src/organizer.py` (Pass 3): Will ingest `config.routing` to replace the highly conditional `if/else` hierarchy logic.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-Organization Logic (Grouping & Routing)*
*Context gathered: 2026-07-01*
