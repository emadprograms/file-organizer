# Phase 10: close-gaps-wire-correct-sanitize-filename-and-fix-llm-500-er - Context

**Gathered:** 2026-07-05T23:50:00+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire correct `sanitize_filename` and fix LLM 500 error handling behavior to gracefully handle and recover from pipeline failures.

</domain>

<decisions>
## Implementation Decisions

### Sanitize Filename Location
- **D-01:** Standardize `sanitize_filename` implementation in `src/core/utils.py`. Delete or deprecate duplicate implementations (e.g. in `src/fs_utils.py`).

### LLM 500 Error Handling & Recovery
- **D-02:** Instead of routing failed documents to `Unassigned`, failing documents due to 500 errors must **abort the entire pipeline and fail the file**.
- **D-03:** The consecutive 500 error counter must remain global for the entire pipeline run. If the limit is reached, fail out.
- **D-04:** Ensure failure states allow the user to easily pick up where they left off without manually cleaning up partial successes or `Unassigned` fallback files.

### the agent's Discretion
- For the filename sanitization standardization, you decide how best to organize the imports and delete the old files.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Error Handling
- `src/llm/llm.py` — Location of consecutive 500 errors counter and limits.
- `src/processing/routing.py` / `src/processing/pipeline.py` — Location where the fail/abort logic will replace the `Unassigned` fallback.

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/core/utils.py`: Target location for centralizing `sanitize_filename`.

### Established Patterns
- Checkpoint/resume (DIFF-02): Aborting the pipeline upon LLM limits relies on resuming capabilities so the user doesn't lose progress. Ensure the abort mechanism is clean.

### Integration Points
- LLM limit exhaustion in boundary detection or grouping/routing must cascade an error up to the main pipeline to safely abort, rather than catching and ignoring.

</code_context>

<specifics>
## Specific Ideas

- "don't give up on that chunk. fail that file. so that when I try that file again, I can continue from where I left... if anything fails, I should always be able to pick up where I left off form."

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-close-gaps-wire-correct-sanitize-filename-and-fix-llm-500-er*
*Context gathered: 2026-07-05T23:50:00+03:00*
