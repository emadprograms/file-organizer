# Phase 2: Pass 1 — Document Cleaning - Context

**Gathered:** 2026-07-03
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase handles parsing the JSON report, resolving and canonicalizing tenant names (using anchor documents), generating tenant timelines, inferring missing dates, assigning pages to tenant timelines, and grouping unresolvable pages into an Unassigned folder. It ensures every page has a canonical tenant and resolved date before grouping begins.

</domain>

<decisions>
## Implementation Decisions

### Name Canonicalization Strategy
- **D-01:** Use RapidFuzz to merge obvious OCR typos first, then send the remainder to the LLM for translation/hard cases (as recommended in STACK.md) to save tokens and improve efficiency.

### Null Date Inference
- **D-02:** Infer missing dates by looking for the closest dated page by absolute index distance, tie-breaking by looking backward if distances are equal.

### Unassigned Folder Naming
- **D-03:** Use a "Year-Month" granularity for the inferred period (e.g., `Unassigned (2020-05)`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/REQUIREMENTS.md` - Core requirements for CLN-01 through CLN-10.
- `.planning/PROJECT.md` - Key decisions (Anchor-based resolution, timeline authority).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/llm_client.py` - Use for all LLM calls (configured in Phase 1).
- `src/logger.py` - Use for structured audit logging.

### Established Patterns
- Strict rate limiting and error handling via `llm_client.py`.
- No async LLM calls.

### Integration Points
- Extends the core CLI defined in Phase 1 to process the JSON report.

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

*Phase: 2-Pass 1 — Document Cleaning*
*Context gathered: 2026-07-03*
