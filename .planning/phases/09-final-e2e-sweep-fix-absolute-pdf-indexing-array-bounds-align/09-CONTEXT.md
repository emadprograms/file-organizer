# Phase 09: final-e2e-sweep-fix-absolute-pdf-indexing-array-bounds-align - Context

**Gathered:** 2026-07-05T22:23:56+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers critical bug fixes for end-to-end processing, focusing on PDF indexing alignment (0-based vs 1-based), array bounds, date resolution consistency, logging transparency for LLMs, and pipeline structural integrity.

</domain>

<decisions>
## Implementation Decisions

### PDF Page Indexing Strategy
- **D-01:** Standardize on 0-based indexing internally. Convert input to 0-based immediately, work in 0-based throughout the pipeline, and convert to 1-based only for output.
- **D-02:** Use strict array bounds validation. Abort processing if a referenced page is out of bounds to prevent silent data loss or mangled outputs.
- **D-03:** Fail reconciliation completely if any page is dropped. Require the pipeline to account for every single page from input to output, otherwise fail the entire house processing.
- **D-04:** Centralize the logic for index bounds resolution and 0-based conversion in a utility module for consistency everywhere.

### LLM Logging Format
- **D-05:** Write detailed LLM request/responses to separate JSON files inside a `logs/traces/` directory, keeping the main log readable.
- **D-06:** Explicitly parse the token usage metadata and print it at INFO level in the main log to track costs and limits.
- **D-07:** Log errors to trace files and warn in the console. Save the exact malformed output in a `.error.json` trace file.

### Pipeline Architecture Refactoring
- **D-08:** Apply targeted, precise fixes to the exact locations where array bounds fail and indexing is mismatched, minimizing regression risk.
- **D-09:** Ensure all dates are fully resolved to absolute values in Pass 1, so Pass 2 and Routing never have to guess or recalculate.
- **D-10:** Use safe defaults for bounds/index errors at runtime. If an indexing bug occurs in production, gracefully dump the affected pages to the "Unassigned" folder rather than crashing the whole pipeline.

### The Agent's Discretion
None

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None specifically highlighted; use existing logging utilities and core pipeline orchestration logic.

### Established Patterns
- Centralized LLM client in `llm.py`.
- Pipeline progression with defined Pass 1 and Pass 2 structure.
- Unassigned folder is explicitly handled for unresolvable content.

### Integration Points
- Index conversion logic will hook directly between the parsed JSON payload and PyMuPDF slicing.

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

*Phase: 09-final-e2e-sweep-fix-absolute-pdf-indexing-array-bounds-align*
*Context gathered: 2026-07-05T22:23:56+03:00*
