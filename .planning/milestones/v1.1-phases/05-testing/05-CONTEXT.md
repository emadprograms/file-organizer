# Phase 5: Testing - Context

**Gathered:** 2026-06-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Adds comprehensive unit tests for core application logic and integration tests for the API fallback chain (Gemini -> OpenRouter -> Groq), ensuring code hardening and validating the implementation.

</domain>

<decisions>
## Implementation Decisions

### Testing Strategy
- **D-01:** Leverage the existing `.cache.json` for a record/replay approach for integration tests, keeping the environment close to real execution and reusing existing caching code.

### Fallback Integration
- **D-02:** Hit the real APIs with dummy/invalid API keys to trigger actual errors and test the fallback routing chain directly.

### Coverage & CI
- **D-03:** Run tests locally for now. Do not enforce a specific test coverage threshold or set up automated CI runs (e.g. GitHub Actions) yet.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Defines TEST-01 (add comprehensive unit and integration tests).

### Codebase & Testing Conventions
- `.planning/codebase/TESTING.md` — Explains pytest usage, test structure (tests/ vs scripts/), and caching logic for LLM testing.
- `.planning/codebase/CONVENTIONS.md` — Covers error handling (custom exceptions `LLMFailureError`) and fallback logic patterns.
- `.planning/codebase/STRUCTURE.md` — Outlines directory structure relevant to test placement.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pytest`: Already configured framework.
- `.cache.json` & Pipeline Caching: Allows mocking APIs seamlessly without hitting external endpoints, providing a record/replay mechanism.

### Established Patterns
- Nested `try-except` blocks: Used for fallback routing; critical to test API key invalidation paths.
- `Pydantic BaseModel`: Used for structured output; parsing logic should be tested.

### Integration Points
- `src/llm.py`: Tests should target API wrappers and specific custom exceptions like `LLMFailureError` and `InvalidResponseError`.
- `src/pipeline.py`: Main engine where fallback logic occurs; needs testing across the Gemini -> OpenRouter -> Groq chain.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches using `pytest`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 5-Testing*
*Context gathered: 2026-06-28*
