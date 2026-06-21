# Phase 2: LLM Integration - Context

**Gathered:** 2026-06-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Interface with Gemma 4 31b to analyze extracted Arabic text and classify documents into the proper folders/residents while maintaining multipage context.

</domain>

<decisions>
## Implementation Decisions

### API Provider and Schema
- **D-01:** Access Gemma 4 31b using a Google API key (Google AI Studio).
- **D-02:** Use the Google Gen AI SDK (`@google/genai` or similar). Try to rely on its native JSON schema capabilities if supported by the model tier; otherwise, fallback to strict system prompt engineering with retry logic.

### Page Context Strategy
- **D-03:** Use a dynamic sliding window approach: accumulate pages into the context window and send them together until the LLM explicitly flags that the topic has changed.

### Execution Order & Rate Limiting
- **D-04:** Process pages strictly sequentially. This is slower but guarantees the sliding window and context accumulation work correctly. 
- **D-05:** Implement exponential backoff for Google API rate limits.

### Arabic Name Normalization
- **D-06:** The LLM should intelligently normalize Arabic names (e.g. grouping "Al Muhammad" and "Muhammad" together) to ensure consistent folder creation. Do not blindly extract exact text; understand the referent.

### Fallback Behavior
- **D-07:** Do not drop malformed responses into an "Uncategorized" folder. If the LLM output is invalid, automatically retry the prompt.

### Generic Letters & "Amar Takhsees"
- **D-08:** The LLM must output a specific constant like `"Resident": "NONE"` for general house letters and "Amar Takhsees" so they are routed to the root folder.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Definitions
- `.planning/ROADMAP.md` — Active phase definitions and success criteria.
- `.planning/REQUIREMENTS.md` — System requirements LLM-01 through LLM-05.
- `.planning/PROJECT.md` — Core constraints and structural definitions.

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `01-ocr-pdf-pipeline` outputs: The output artifacts from Phase 1 (extracted text, OCR boundaries) are the direct inputs here.

### Established Patterns
- Sequential processing pipeline pattern established in Phase 1.

### Integration Points
- Connecting OCR text extraction directly to the Google Gen AI API calls.
- Feeding the structured JSON output into the filesystem generator (Phase 3).

</code_context>

<specifics>
## Specific Ideas

- The LLM context window will dynamically expand page by page until a topic break is detected.
- Emphasized need to group Arabic names correctly across all pages despite minor prefix/suffix variations.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2-LLM Integration*
*Context gathered: 2026-06-21*
