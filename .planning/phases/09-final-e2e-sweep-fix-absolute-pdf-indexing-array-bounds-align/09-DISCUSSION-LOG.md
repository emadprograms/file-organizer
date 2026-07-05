# Phase 09: final-e2e-sweep-fix-absolute-pdf-indexing-array-bounds-align - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-05T22:23:56+03:00
**Phase:** 09-final-e2e-sweep-fix-absolute-pdf-indexing-array-bounds-align
**Areas discussed:** PDF Page Indexing Strategy, LLM Logging Format, Pipeline Architecture Refactoring

---

## PDF Page Indexing Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Standardize on 0-based internally | Convert input to 0-based immediately, work in 0-based throughout the pipeline, and convert to 1-based only for output. | ✓ |
| Keep 1-based internally | Pass 1-based indices through the pipeline and subtract 1 only exactly at the moment PyMuPDF is called. | |
| Strict validation | Abort processing if a referenced page is out of bounds. | ✓ |
| Lenient with warnings | Cap indices to the maximum available page, log a warning, and continue. | |
| Fail reconciliation completely | Require the pipeline to account for every single page from input to output, otherwise fail the entire house processing. | ✓ |
| Dump missing pages | Collect any unaccounted pages into a generic "Lost & Found" or "Unassigned" folder. | |
| Centralized utility | Create a single function (e.g., in a utils module) responsible for index alignment/conversion. | ✓ |
| Localized at invocation | Keep the conversion logic directly next to the PyMuPDF calls. | |

**User's choice:** Standardize on 0-based internally, Strict validation, Fail reconciliation completely, Centralized utility.
**Notes:** None

---

## LLM Logging Format

| Option | Description | Selected |
|--------|-------------|----------|
| Separate trace files | Write detailed LLM request/responses to separate JSON files inside a `logs/traces/` directory. | ✓ |
| Main log file | Keep everything in a single log file, perhaps using DEBUG level for the raw payloads. | |
| Extract and log token usage | Explicitly parse the token usage metadata and print it at INFO level in the main log. | ✓ |
| Trace files only | Leave the token usage inside the raw trace files. | |
| Log errors to trace files and warn in console | Keep the main console clean with a generic warning, but save the exact malformed output in a `.error.json` trace file. | ✓ |
| Dump to console | Print the exact malformed response to the console. | |

**User's choice:** Separate trace files, Extract and log token usage, Log errors to trace files and warn in console.
**Notes:** None

---

## Pipeline Architecture Refactoring

| Option | Description | Selected |
|--------|-------------|----------|
| Targeted patches | Apply precise fixes to the exact locations where array bounds fail and indexing is mismatched. | ✓ |
| Refactor data flow | Re-architect the data passing between stages to strongly type and enforce bounds checking automatically. | |
| Finalize dates early | Ensure all dates are fully resolved to absolute values in Pass 1, so Pass 2 and Routing never have to guess or recalculate. | ✓ |
| Resolve at output | Leave dates relative until the very end, then resolve them when building the final folder structure. | |
| Safe defaults | If an indexing bug occurs in production, gracefully dump the affected pages to the "Unassigned" folder rather than crashing the whole pipeline. | ✓ |
| Hard crash | Any indexing or bounds error should immediately raise an exception. | |

**User's choice:** Targeted patches, Finalize dates early, Safe defaults.
**Notes:** None

---

## The Agent's Discretion
None

## Deferred Ideas
None
