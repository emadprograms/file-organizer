# Phase 5: decouple-core-pipeline - Context

**Gathered:** 2026-07-02T22:12:00+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

Refactoring `src/llm.py`, `src/organizer.py`, and `src/pipeline.py` to extract domain-specific logic (Bahrain housing) into external config/scripts, leaving the core pipeline fully generic.

</domain>

<decisions>
## Implementation Decisions

### Config Format
- **D-01:** User-defined routing rules will use simple key-value mapping (keys are LLM output categories, values are destination folders) to mirror current program behavior.
- **D-02:** Missing/unmapped categories will route to a 'fallback_folder' defined in the config (acts like an Uncategorized folder).
- **D-03:** Grouping constraints will be specified using max page limit and category sets.
- **D-04:** The configuration file will be validated automatically at pipeline startup using Pydantic schemas.

### Legacy Logic Scripts
- **D-05:** Store fallback Python scripts in a dedicated `scripts/` folder outside `src/` to clearly separate core from custom logic.
- **D-06:** The core pipeline will invoke scripts simply by importing them and calling functions directly (functional approach) to keep it simple.
- **D-07:** Errors within the user-provided fallback scripts will be caught, logged, and the pipeline will use a safe default.
- **D-08:** If the config doesn't specify a fallback script, the pipeline will use a built-in strict default (e.g. standard sequential grouping).

### LLM Prompts
- **D-09:** The domain-specific LLM prompts will be defined in the config using simple string formatting with basic variables like `{text}` (to mirror current behavior).
- **D-10:** LLM extraction schema fields (category, residents, date) will be defined as a list of fields with name, type, and description in the config to dynamically build the Pydantic schema.
- **D-11:** Allowed string category values will be defined in the config and mapped to internal representations dynamically.
- **D-12:** All secondary LLM prompts (semantic clustering, date outlier detection) will be externalized to make the entire LLM layer fully configurable.

### the agent's Discretion
None

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture
- `.planning/codebase/ARCHITECTURE.md` — Defines the pipeline stages (Ingestion, Extraction, Orchestration, Organization) which must remain intact.
- `.planning/codebase/STACK.md` — Core dependencies (PyMuPDF, Pydantic, Tenacity, Google GenAI).

No external specs — requirements fully captured in decisions above
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `UserConfig`: Existing configuration class (used in `src/organizer.py`) that can be extended for LLM prompts and grouping constraints.

### Established Patterns
- `organizer.organize`: Uses `importlib.util` to load python scripts dynamically, which will be replicated for heuristic scripts.
- LLM Provider Routing: `LLMClient` uses an internal routing strategy across models.

### Integration Points
- `src/pipeline.py`: Needs to inject loaded configuration into the passes.
- `src/llm.py`: Needs to stop relying on hardcoded enums and multiline strings, using config parameters instead.
</code_context>

<specifics>
## Specific Ideas

- "just do it like the current program does it" — The externalization should result in the exact same execution flow as the current hardcoded logic.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-decouple-core-pipeline*
*Context gathered: 2026-07-02T22:12:00+03:00*
