# Phase 2: Pipeline Adaptation (Extraction & Cleaning) - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the adaptation of the pipeline's extraction (Pass 1) and cleaning (Pass 1.5) passes to use instructions defined in the user-provided config, replacing hardcoded assumptions.
</domain>

<decisions>
## Implementation Decisions

### Prompt Templating Strategy
- **D-01:** User provides the full prompt in the config, giving them maximum control over how the AI is instructed.

### Dynamic Schema Extraction
- **D-02:** Strict Schema. The user defines the fields and types (string, date, boolean, etc.) in the YAML config. The pipeline dynamically builds a Pydantic model to force the AI to return perfectly typed data, catching formatting errors and retrying.

### Cleaning Rules Definition (Pass 1.5)
- **D-03:** Provide both LLM and Python Scripting strategies. The config lets the user choose whether to use an LLM prompt or a custom Python script for their cleaning pass, offering both simplicity for common cases and power for complex logic (like the original real estate timelines).

### the agent's Discretion
Any implementation details not covered by the above (e.g., exact YAML keys used to define the schema or the Python execution environment sandbox, though safety is not a primary concern for a local CLI tool).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specifications
- `.planning/REQUIREMENTS.md` — Defines requirements for extraction and cleaning (EXT-01, EXT-02).
- `.planning/ROADMAP.md` — Defines phase 2 goals and success criteria.

### Architecture and Structure
- `.planning/codebase/ARCHITECTURE.md` — Overview of pipeline architecture that we must maintain.
- `.planning/codebase/INTEGRATIONS.md` — Explains the integration points with the Google GenAI API.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/schemas.py`: Where the dynamic Pydantic model generation logic should be housed or referenced.
- `src/pipeline.py`: Where the logic for Pass 1 and Pass 1.5 needs to be updated to hook into the configuration instead of running the hardcoded functions.
- `src/extractors.py`: Where the LLM prompt injection currently happens and needs to be replaced with the user's config prompt.

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

*Phase: 2-Pipeline Adaptation (Extraction & Cleaning)*
*Context gathered: 2026-07-01*
