# Phase 11: close-gaps-llm-01-to-llm-08-log-02-out-05-grp-10-wire-correc - Context

**Gathered:** 2026-07-06T08:24:00+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire correct LLMClient error handling, audit logging, unassigned folder naming, and semantic routing to close the remaining gaps for v1.0.

</domain>

<decisions>
## Implementation Decisions

### Audit Log Format (LOG-02)
- **D-01:** Log grouping, routing, and tenant decisions both as an inline summary in `app.log` (for quick reading) and as detailed JSON in `logs/traces/` (for structural analysis).

### Unassigned Period Naming (OUT-05)
- **D-02:** Format the inferred dates in the folder name for unassigned documents using the year and month: `Unassigned (YYYY-MM to YYYY-MM)`.

### Semantic Routing Response (GRP-10)
- **D-03:** The multi-match routing LLM call must return a JSON object containing both `folder` and `reason` to provide a better audit trail and force the LLM to think.

### the agent's Discretion
- Implementation details of how to pass the JSON schema to the Gemini API for semantic routing.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Error Handling & Audit
- `src/logger.py` — Logging setup for `app.log` and the traces directories.
- `src/processing/routing.py` — Multi-match category LLM routing logic implementation.

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- JSON trace logging implemented in Phase 09 for `llm.py` can be reused or extended for grouping, routing, and tenant resolution decisions.

### Established Patterns
- LLM outputs are captured structured as JSON for debugging, and LLM limits/errors are logged at INFO/WARN levels accordingly.

### Integration Points
- Routing LLM call inside `src/processing/routing.py` needs to update its Pydantic schema (or instructions) to require a `reason` field alongside the `folder`.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-close-gaps-llm-01-to-llm-08-log-02-out-05-grp-10-wire-correc*
*Context gathered: 2026-07-06T08:24:00+03:00*
