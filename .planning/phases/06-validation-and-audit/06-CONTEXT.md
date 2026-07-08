# Phase 06: Validation and Audit - Context

**Gathered:** 2026-07-09
**Status:** Ready for Planning

<domain>
## Phase Boundary

This phase serves as the quality gate for the 'Logging Overhaul' milestone. The objective is to audit the changes implemented in Phase 04 (Infrastructure) and Phase 05 (Migration) to ensure 100% compliance with the new logging standards. It focuses on verification rather than implementation, ensuring that no legacy patterns (like `print` calls) remain and that the telemetry system behaves predictably across different verbosity levels.

</domain>

<decisions>
## Audit Criteria

### 1. Structural Compliance
- **Logger Naming:** Every module in `src/` and `tests/` must use `logger = logging.getLogger(f"file_organizer.{__name__}")`.
- **Variable Consistency:** The variable name `logger` must be used consistently (no `log`, `logging`, etc.).
- **Print Removal:** Zero `print()` statements should exist in `src/` for system telemetry. Only `rich.console.print` is permitted for user-facing output.

### 2. Functional Validation
- **Dual-Log Integrity:** 
    - `app.log` must contain human-readable INFO+ logs.
    - `debug.log` must be valid JSONL containing DEBUG+ logs.
- **Noise Suppression:** 
    - When `verbose=False`, logs from `openai`, `google-genai`, `urllib3`, and `httpcore` must be suppressed (WARNING+).
    - When `verbose=True`, only `file_organizer` hierarchy logs should be prominent (Strict Whitelist).
- **Error Capturing:** All catch-blocks must use `logger.exception()` instead of `logger.error(f"Error: {e}")` to ensure stack traces are preserved in `debug.log`.

### 3. Telemetry & UI Separation
- **Console vs. Log:** Verify that no system-level telemetry (e.g., "Connecting to API...") is printed to the console via `rich` if it is already captured by the logger, unless it's a primary progress indicator.
- **Trace Logs:** Verify `traces.jsonl` is correctly populated with decision-trace payloads using `log_decision_trace`.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/phases/04-logging-infrastructure-refactor/04-CONTEXT.md` — Infrastructure specs.
- `.planning/phases/05-global-logger-migration/05-CONTEXT.md` — Migration rules.
- `src/logger.py` — The implementation under audit.
</canonical_refs>

<risks>
## Identified Risks & Gray Areas

- **Test Log Leakage:** There is a risk that `tests/` might still contain `print` statements used for debugging that were missed during migration.
- **Rich Console Over-usage:** The boundary between "User-facing flow" and "System telemetry" can be subjective; some `console.print` calls might actually be telemetry that belongs in the logs.
- **Performance:** The overhead of JSONL serialization for every DEBUG message in high-frequency loops should be monitored.

</risks>

<recommendations>
## Recommendations for Planning

- **Automated Grep Audit:** Use regex searches to find any remaining `print(` (excluding `console.print`) across the codebase.
- **Log Diffing:** Run the application in both `verbose=True` and `verbose=False` modes and diff the `debug.log` files to ensure the blacklist/whitelist is working.
- **Exception Sampling:** Trigger known error paths to verify that `debug.log` contains full tracebacks via `logger.exception`.
</recommendations>
