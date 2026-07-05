# Phase 07: cross-phase-integration-fixes-tenant-date-mapping-relative-i - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning

## Phase Boundary

Resolve cross-phase integration gaps between document cleaning and grouping phases, including fixing zero-indexed vs one-indexed page mapping logic, handling pipeline fallbacks gracefully, adding verbosity and mock-testing CLI flags, and formatting detailed dry-run outputs.

## Implementation Decisions

### Relative vs Absolute Indexing
- **D-01:** Normalize everything to 0-indexed internally immediately after parsing, only convert to 1-indexed for logging/UI.

### Dry-Run output format
- **D-02:** Show a concise tree of planned folders and files, omitting LLM reasoning to keep it clean.

### Tenant/Date Mapping fallbacks
- **D-03:** Route to 'Unassigned' folder to guarantee pipeline completion, flagging it in the logs.

### CLI flag design
- **D-04:** Add both `--verbose` (output full LLM prompt/responses and verbose logs) and `--skip-llm` (mock LLM responses for faster layout/routing testing) alongside `--dry-run`.

### the agent's Discretion
None

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above.

## Existing Code Insights

### Reusable Assets
- `pdf_utils.py` / `pymupdf` bindings: Needs modification to ensure PyMuPDF correctly handles the 0-indexed boundaries internally.
- `models.py` / `schemas.py`: Add new flags or mock configurations to `Config` structures.

### Established Patterns
- Existing error handling and fallback patterns (e.g. routing to `13_others` on multiple errors) should be modeled for the Unassigned fallback.

### Integration Points
- `cli.py` or `organize.py` argument parsing needs to accept `--verbose` and `--skip-llm` flags and propagate them to the LLM client and logger.
- The boundary merging logic must consistently assume 0-indexed arrays and pages.

## Specific Ideas

No specific requirements — open to standard approaches

## Deferred Ideas

None — discussion stayed within phase scope

---

*Phase: 07-cross-phase-integration-fixes-tenant-date-mapping-relative-i*
*Context gathered: 2026-07-05*
