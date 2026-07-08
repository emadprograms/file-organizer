# Discussion Log: Phase 04 Logging Infrastructure Refactor

**Date:** 2026-07-08
**Phase:** 04

## Decisions Captured

### LogContext Design
- **User Selection:** Singleton Class.
- **Notes:** Ensure an explicitly initialized, immutable `run_dir` across the entire application lifecycle.

### Debug Log JSON Schema
- **User Selection:** Standard Detailed.
- **Notes:** Include timestamp, level, logger name, message, filename, and line number for machine-readability and efficient debugging.

### Noise Suppression Strategy
- **User Selection:** Dynamic (Verbose-based).
- **Notes:** If `verbose` flag is present, use a strict whitelist of the `file_organizer` hierarchy. Otherwise, use a permissive blacklist of known noisy libraries.

### Trace Logging Integration
- **User Selection:** Claude's Discretion.
- **Notes:** Decide based on performance and structural fit.

---

## Deferred Ideas
- **Global Logger Migration:** Deferred to Phase 05.
