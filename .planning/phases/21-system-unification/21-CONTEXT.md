# Phase 21: System Unification - Context

**Gathered:** 2026-07-19T21:35:25+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

Port file-categorizer logic for `_report.json` generation using Gemini 3.1 FL and OCR to the main repository.
</domain>

<decisions>
## Implementation Decisions

### Module Placement
- **D-01:** Place the new logic in `src/categorization.py` — Runs before `cleaning.py`, keeps `main.py` lean and preserves functional pipeline.

### LLM Client Integration
- **D-02:** Adapt to use existing `LLMClient` wrapper — Maintains consistency, retry logic, and JSON schema enforcement instead of keeping standalone API calls.

### Image Processing and Extraction Strategy
- **D-03:** Port `image_processing.py` and `ai_classification.py` exactly as they are without text-based OCR fallbacks. Render pages to high-res images, use OpenCV cleaning pipeline, and send optimized images directly to Gemini's vision endpoint.

### Bypass Logic (CAT-02)
- **D-04:** Look for existing `_report.json` co-located with the PDF (in the exact same directory) to bypass extraction.

### the agent's Discretion
None — user made explicit choices for all areas.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture and Requirements
- `.planning/REQUIREMENTS.md` — Defines CAT-01 and CAT-02.
- `.planning/PROJECT.md` — Defines the hybrid architecture decision.
- `.planning/codebase/ARCHITECTURE.md` — Defines pipeline layers (`src/cleaning.py` and `src/processing/`) and the existing resilient `LLMClient` wrapper.

### Source Logic to Port
- `../file-categorizer/src/image_processing.py` — The highly tuned OpenCV image processing pipeline.
- `../file-categorizer/src/ai_classification.py` — The Gemini vision endpoint communication logic.
*(Note: Downstream agents MUST read these files to port the code exactly.)*

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/llm/client.py`: The `LLMClient` wrapper should replace the standalone Gemini API calls from the source repository.

### Established Patterns
- Functional data pipeline: The v2.0 refactor established a functional pipeline (`cleaning.py`, `processing/pipeline.py`) which must be preserved.

### Integration Points
- `src/main.py`: The entry point will orchestrate the new `src/categorization.py` module before calling `src/cleaning.py`.

</code_context>

<specifics>
## Specific Ideas

- **CRITICAL NOTE FOR PLANNER:** When making the plan, keep in mind that the codebase already exists. We do not want to create the logic from scratch. We only want to port the code from `file-categorizer` into a folder in this repo to maintain consistency. WE ARE NOT BUILDING FROM SCRATCH. WE ARE ONLY PORTING TO THIS REPO.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 21-system-unification*
*Context gathered: 2026-07-19T21:35:25+03:00*
