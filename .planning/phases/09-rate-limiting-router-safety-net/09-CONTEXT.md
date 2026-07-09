# Phase 09: Rate Limiting & Router Safety Net - Context

**Gathered:** 2026-07-09
**Status:** Ready for planning

<domain>
## Phase Boundary
The goal of this phase is to implement a "Correctness First" safety net for all LLM interactions. The system must handle rate limits and server errors deterministically, eliminate all "graceful" fallbacks that lead to mis-routed documents, and ensure the program halts immediately upon unrecoverable errors to prevent data corruption.

</domain>

<decisions>
## Implementation Decisions

### 1. Global LLM Resilience Logic (Deterministic)
All LLM calls in the system must follow this strict logic:
- **Error 429 (Rate Limit):** 
  - Action: Wait exactly **65 seconds**.
  - Retries: Up to **3 times**.
  - Switching: Do NOT switch providers.
  - Termination: If 3 retries fail, **HALT PIPELINE immediately**.
- **Error 500/503 (Server Errors):** 
  - Action: Wait exactly **15 seconds**.
  - Switching: **Switch provider** immediately using the Alternating Cycle (see below).
  - Retries: Up to **3 times**.
  - Termination: If 3 retries fail, **HALT PIPELINE immediately**.
- **Error 401/403 (Auth/API Key):** 
  - Action: **HALT PIPELINE immediately** (no retries).

### 2. Provider Rotation (Triggered by 500s ONLY)
When a 500 error occurs, the system rotates through providers to balance load and avoid downtime.
- **The Sequence:** Gemini $ightarrow$ [Secondary] $ightarrow$ Gemini $ightarrow$ [Other Secondary].
- **The Alternation:** The "Secondary" provider alternates between **Groq** and **OpenRouter** for every new request.
  - Request 1: Gemini $ightarrow$ Groq $ightarrow$ Gemini $ightarrow$ OpenRouter
  - Request 2: Gemini $ightarrow$ OpenRouter $ightarrow$ Gemini $ightarrow$ Groq

### 3. "Correctness First" Failure Model
- **Remove Lockout Behavior:** Completely remove the `consecutive_routing_failures` logic in `src/processing/routing/router.py`.
- **No Fallbacks:** Delete all logic that routes documents to `13_others` as a "fallback" when the LLM fails.
- **Hard Stop:** The system must not "skip" a document or "gracefully" fail. Any unrecoverable error must trigger an immediate stop of the application.

### 4. Continuity and Checkpoints
- **Halt Strategy:** The pipeline must halt immediately on error to protect the current state.
- **Future Resumption:** While the state-saving (Checkpointing) is the primary focus of Phase 10, Phase 09 must ensure that errors are raised as hard exceptions that can be caught by a future checkpoint manager.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & Requirements
- `.planning/ROADMAP.md` — Phase 09 success criteria.
- `.planning/REQUIREMENTS.md` — Requirements RES-01, RES-02, RES-03.

### Existing Implementation
- `src/llm/llm.py` — Current `LLMClient` and retry logic.
- `src/processing/routing/router.py` — Current routing logic and lockout mechanism.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LLMClient` in `src/llm/llm.py` is the central point for all LLM requests. Modifying this class will apply the new resilience logic globally.
- `tenacity` library is already integrated; it should be updated from exponential backoff to fixed-time waits.

### Integration Points
- The removal of the `consecutive_routing_failures` lockout in the router is a surgical edit to `src/processing/routing/router.py`.

</code_context>

<specifics>
## Specific Ideas
- **Rotation Logic:** The rotation state (which secondary provider to use first) should be tracked in the `LLMClient` to persist across requests.
- **Exception Hierarchy:** Ensure that the `LLMFailureError` or a new `CriticalPipelineError` is raised when a halt is required, to prevent the pipeline from continuing to the next document.

</specifics>

<deferred>
## Deferred Ideas
- **State-based Resumption:** Detailed implementation of saving and loading state to resume from a specific page is deferred to Phase 10.

</deferred>

---
*Phase: 09-Rate Limiting & Router Safety Net*
*Context gathered: 2026-07-09*
