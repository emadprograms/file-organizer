# Phase 08: "True Until Proven Guilty" Grouping Logic - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

The goal of this phase is to shift the document grouping logic from structural detection to narrative/theme detection. The system will assume pages continue the same document ("True Until Proven Guilty") unless a definitive shift in the central theme of the subject is detected.

</domain>

<decisions>
## Implementation Decisions

### Grouping Matrix (Hybrid Logic)
The grouping process will be routed based on the document category:
- **Letters**: Subject-Based Grouping. The LLM will compare the `subject` field of consecutive pages. Continuity is assumed as long as the central theme of the subject remains the same. Changes in sender, date, or the presence of tables do NOT trigger a split.
- **Forms**: Standard Grouping. Use the existing `content_explanation` based boundary detection.
- **Contracts**: Always Together. Hard-coded logic to group all consecutive contract pages into one document.
- **ID Cards**: Always Together. Hard-coded logic to group all consecutive ID card pages into one document.
- **Utility Bills**: Always Separate. Hard-coded logic to treat every page as a distinct document.
- **Others**: Precision Content-Based. Use `content_explanation` but process in strict **chunks of 2** to ensure high-precision boundary detection.

### Letter Prompting Strategy
For the "Letters" category:
- **Metadata-Driven**: Instead of full content explanations, the LLM will be provided with the `subject` field.
- **Narrative Frame**: The prompt will instruct the LLM to identify "Correspondence Stories." A split only occurs on a "Hard Reset"—a definitive shift in the central theme of the subject.

### Prompt Management
- **Configuration-Based**: Grouping prompts for "Letters", "Forms", and "Others" will be moved to a dedicated configuration file (e.g., `src/processing/grouping/config.py`) to allow for iterative tuning without modifying core logic.

### Verification Strategy
Verification will focus on three pillars:
1. **Letter Continuity**: New golden test cases where pages have slightly varying `subject` strings but share a central theme $ightarrow$ verify they remain as one group.
2. **Hard-Coded Rule Validation**: Unit tests to ensure Contracts/IDs are grouped and Bills are split without LLM invocation.
3. **Precision Window**: Verify "Other" categories are processed in windows of 2.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & Requirements
- `.planning/ROADMAP.md` — Phase 08 success criteria.
- `.planning/REQUIREMENTS.md` — Requirements PRMPT-01, PRMPT-02, PRMPT-03.

### Existing Implementation
- `src/processing/grouping/core.py` — Current grouping and shrink logic.
- `src/core/schemas.py` — `DocumentGroup` and `GroupingResponse` definitions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `GroupingResponse` (Pydantic): Already handles structured output for boundaries.
- `process_with_shrink`: The infrastructure for iterating through pages exists; only the internal `_process_chunk` and the routing logic need modification.

### Established Patterns
- **Resilient LLM Calls**: The system already uses `LLMClient` with retries.
- **Trace Logging**: Grouping decisions are already logged via `log_decision_trace`.

### Integration Points
- The modification happens within `src/processing/grouping/core.py` and will introduce a new config file in the same directory.

</code_context>

<specifics>
## Specific Ideas

- **The "Table Trap"**: Explicitly instruct the LLM that tables are transparent and do not signal a subject shift.
- **Correspondence Stories**: Frame the task as identifying a conversation/story rather than a physical document.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-"True Until Proven Guilty" Grouping Logic*
*Context gathered: 2026-07-08*
