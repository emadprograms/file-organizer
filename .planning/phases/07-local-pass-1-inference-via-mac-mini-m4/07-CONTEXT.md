# Phase 7: Local Pass 1 Inference via Mac Mini M4 - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Drastically speed up Pass 1 Vision Extraction by moving it locally using Qwen2-VL-7B-Instruct and an OpenAI-compatible API endpoint, bypassing Google API rate limits.

</domain>

<decisions>
## Implementation Decisions

### Local Server Stack
- **D-01:** Use LM Studio to run Qwen2-VL-7B-Instruct on the Mac Mini. The built-in OpenAI API server will be utilized.
- **D-02:** Stick with Qwen2-VL-7B-Instruct as it is best suited for the Arabic document OCR use case.

### Fallback Strategy
- **D-03:** Hybrid fallback strategy. If the local Qwen2-VL model fails or hangs, the system will fall back to Gemini 4 26b. (Note: Gemini 4 31b and Gemini 2.5 Flash are being retired).

### Client Integration Approach
- **D-04:** Use the official `openai` Python package to connect the pipeline to the local LM Studio endpoint, ensuring robust handling of schemas and retries.

### the agent's Discretion
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
- `src/llm.py`: Existing `_route_llm_call` handles retries, rate limits, and fallback logic, which can be adapted or bypassed for the local OpenAI client.

### Established Patterns
- `src/schemas.py`: Uses Pydantic schemas (`PageClassification`) for structured JSON extraction. The `openai` client supports `response_format` for structured outputs, mapping well to these schemas.

### Integration Points
- `GemmaClient.classify_page` in `src/llm.py` needs to be refactored to first try the local OpenAI endpoint, then fall back to the existing Gemini logic.
</code_context>

<specifics>
## Specific Ideas

- The user specifically requested to retire `gemini 4 31b` and `gemini 2.5 flash` from the fallback mechanism, using exclusively `gemini 4 26b` for cloud fallbacks.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-Local Pass 1 Inference via Mac Mini M4*
*Context gathered: 2026-06-24*
