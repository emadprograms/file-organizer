# Phase 04: Logging Infrastructure Refactor - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Establishing an isolated, unified, and structured logging system that eliminates third-party noise. This phase focuses on the core infrastructure (LogContext, setup_logging, and handler configuration) and does not include the migration of every module's logger calls (which is deferred to Phase 05).

</domain>

<decisions>
## Implementation Decisions

### LogContext Design
- **D-01:** Use a Singleton class for `LogContext` to ensure an explicitly initialized, immutable `run_dir` across the entire application lifecycle.

### Debug Log Schema
- **D-02:** Use a "Standard Detailed" JSONL schema for `debug.log`, including: `timestamp`, `level`, `name` (logger name), `message`, `filename`, and `lineno`.

### Noise Suppression Strategy
- **D-03:** Suppression behavior depends on the `verbose` flag:
    - If `verbose=True`: Use a **Whitelist (Strict)** approach, allowing ONLY the `file_organizer` logger hierarchy to ensure zero noise from external libraries.
    - If `verbose=False`: Use a **Blacklist (Permissive)** approach, blocking only known noisy libraries (e.g., `openai`, `google-genai`, `urllib3`) to allow other potentially useful system logs.

### Claude's Discretion
- **Trace Logging Integration:** The user has left the integration of `traces.jsonl` to Claude's discretion. I will evaluate whether a custom `logging.Handler` or a specialized separate writer is more appropriate based on the performance requirements of the trace logs.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Project Goals
- `.planning/PROJECT.md` — High-level project goals and dual-format logging decision.
- `.planning/REQUIREMENTS.md` — Detailed functional requirements for the Logging Overhaul (Isolation, Unified Run Context, Dual-Format, Codebase Integration).

### Existing Implementation
- `src/logger.py` — Current logging setup and trace writer implementation.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/logger.py`: The existing `setup_logging` and `_write_jsonl_trace` logic can be adapted into the new infrastructure.

### Established Patterns
- **Dual-format logging:** The project already utilizes `app.log` (plain text) and `debug.log` (standard text). The transition to JSONL for `debug.log` is a structural change.
- **Trace logs:** The project uses a specialized JSONL writer for `traces.jsonl`.

### Integration Points
- `src/organize.py`: The main entry point where `setup_logging` is called.
- All modules utilizing `logging.getLogger()`: These will be migrated in Phase 05.

</code_context>

<specifics>
## Specific Ideas

- No specific implementation constraints beyond the decisions captured above.

</specifics>

<deferred>
## Deferred Ideas

- **Global Logger Migration:** Updating every module to use hierarchical logger naming is deferred to Phase 05.

</deferred>

---

*Phase: 04-Logging Infrastructure Refactor*
*Context gathered: 2026-07-08*
