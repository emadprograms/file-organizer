# Phase 3: API Key Cycling & Telemetry - Context

**Gathered:** 2026-06-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement robust API key cycling across 45 keys, tracking capacity preemptively, avoiding rate limits via precise request timing, and outputting diagnostic telemetry to distinguish token vs request limit exhaustion.

</domain>

<decisions>
## Implementation Decisions

### Key Storage & Loading
- **D-01:** Keys will be loaded via a comma-separated list in `.env` (`GEMINI_API_KEYS=key1,key2...`).

### Cycling Trigger
- **D-02:** Track Tokens-Per-Minute (TPM) per key and switch preemptively before hitting the limit, given the large document sizes.

### Telemetry Output
- **D-03:** Output diagnostics to both a dedicated `telemetry.log` file and a summary view in the Tkinter GUI.

### Diagnostic Metrics
- **D-04:** Track Token usage (TPM), Requests (RPM), request latency, and granular error details (differentiating between token limits and request limits).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core Requirements
- `.planning/REQUIREMENTS.md` — Defines HARD-01 and HARD-03 goals for Phase 3.
- `.planning/ROADMAP.md` — Defines the phase success criteria.

### Implementation Context
- `src/llm.py` — Current rate limit and API client logic (`GemmaClient`), including `global_cooldown_until` and `cooldown_keys`.
- `src/pipeline.py` — Pipeline usage of `GemmaClient` showcasing concurrency limits.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `GemmaClient` in `src/llm.py`: Current rate-limit handling and backoff logic.
- `src/gui.py` (assumed based on Tkinter usage): GUI structure for adding the telemetry summary tab.

### Established Patterns
- Uses `threading.Lock()` for `GemmaClient` rate limiting.
- ThreadPoolExecutor manages page processing concurrency in `src/pipeline.py`.
- Round-robin cycling through `cooldown_keys`.

### Integration Points
- Tkinter GUI needs a new tab/panel for the Telemetry summary.
- The `GemmaClient._get_client_and_key()` and `_report_failure()` methods need TPM integration.

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

*Phase: 3-API Key Cycling & Telemetry*
*Context gathered: 2026-06-23*
