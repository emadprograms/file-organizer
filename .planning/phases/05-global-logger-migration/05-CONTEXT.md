# Phase 05: Global Logger Migration - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Migration of the entire codebase to use the newly implemented hierarchical logging system. This phase focuses on updating all logger instantiations to the `file_organizer.{__name__}` pattern, converting remaining `print()` calls to proper logging levels, and clarifying the boundary between system telemetry (loggers) and user-facing CLI output (Rich console).

</domain>

<decisions>
## Implementation Decisions

### Logger Hierarchy Migration
- **D-01:** Use a **Strict Hierarchical** approach: every module must use `logger = logging.getLogger(f"file_organizer.{__name__}")`.
- **D-02:** Perform a **Single-Pass Migration** across all `.py` files in `src/` and `tests/` for consistency.
- **D-03:** Standardize the logger variable name to `logger` across the entire project (replacing `log` or other variations).
- **D-04:** Include the `tests/` directory in the migration to ensure test logs are also correctly categorized.

### Print-to-Logger Conversion
- **D-05:** Implement **Strict Conversion**: all `print()` calls meant for system state or errors are moved to `logger.info()`, `logger.warning()`, or `logger.error()`.
- **D-06:** Map error prints (e.g., `print(f"ERROR: {e}")`) to `logger.exception(e)` to ensure full stack traces are captured in `debug.log`.
- **D-07:** Map warning prints to `logger.warning()`.
- **D-08:** Perform an **Exhaustive Search & Replace** across all of `src/` to ensure no system-level `print` statements remain.

### Rich Console vs. Logger
- **D-09:** Maintain **Strict Separation**: `rich.console` is used ONLY for primary user-facing flow (progress, results, critical errors). All other telemetry goes to `logger`.
- **D-10:** Standardize all user-facing CLI output on `console.print` to ensure consistent formatting.
- **D-11:** Sync console output verbosity with the global `verbose` flag via `setup_logging`.

### Claude's Discretion
- The implementation of the `verbose` flag sync for the `rich` console is left to Claude's discretion (e.g., whether to wrap `console.print` or use a custom console handler).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Goals & Requirements
- `.planning/PROJECT.md` — High-level project goals and dual-format logging decision.
- `.planning/REQUIREMENTS.md` — Detailed functional requirements for the Logging Overhaul.

### Phase 04 Infrastructure
- `.planning/phases/04-logging-infrastructure-refactor/04-CONTEXT.md` — Decisions on `LogContext`, noise suppression, and JSONL schemas that this migration must align with.
- `src/logger.py` — The core logging infrastructure implemented in Phase 04.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/logger.py`: The `setup_logging` function is the sole entry point for configuration.

### Established Patterns
- **Hierarchical Logging:** The pattern `logging.getLogger(f"file_organizer.{__name__}")` is established as the project standard.
- **Dual-Format Logging:** `app.log` (plain text) and `debug.log` (JSONL) are already configured.

### Integration Points
- Every module in `src/` and `tests/` that instantiates a logger.
- All `print()` calls in `src/`.
- `rich.console` usage throughout the application.

</code_context>

<specifics>
## Specific Ideas

- No specific requirements — open to standard approaches for the migration pass.

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-global-logger-migration*
*Context gathered: 2026-07-08*
