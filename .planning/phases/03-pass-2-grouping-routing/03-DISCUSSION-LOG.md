# Phase 3: Pass 2 — Grouping & Routing - Discussion Log

**Date:** 2026-07-04

> **Note:** This log is for human reference and audit purposes. Downstream agents (researcher, planner, executor) consume the CONTEXT.md file, not this log.

## Discussed Areas

### 1. Overlap Merge Resolution
**Options presented:**
- Trust the chunk where the document started (Chunk 1) — it has the context of the document's origin.
- Trust the new chunk (Chunk 2) — it has more forward-looking context to know if the topic shifted.
- Require a strict match — if they disagree on the boundary, retry the LLM grouping for that overlap.

**User selected:** Trust the chunk where the document started (Chunk 1) — it has the context of the document's origin.

**Notes:** Chunk 1 will be authoritative for the overlap page to maintain continuity from the document's origin.

---

### 2. Multi-match Routing Fallback
**Options presented:**
- Fallback to the generic "others" sub-folder within that tenant's directory.
- Retry the LLM call once with stricter constraints, then fallback to "others" if it still fails.
- Assign it to the first allowed folder in the category's mapping list by default.

**User selected:** Retry the LLM call once with stricter constraints, then fallback to "others" if it still fails.

**Notes:** Adds resilience to the LLM routing step before defaulting to the catch-all folder.

---

### 3. Verification Failure Handling
**Options presented:**
- Treat it like a 500 error: shrink the chunk size and retry, failing the pipeline after 10 total attempts.
- Fallback to treating every page in the failing chunk as its own single-page document (safe degradation).
- Hard fail the pipeline immediately so a human can inspect the problematic pages.

**User selected:** Treat it like a 500 error: shrink the chunk size and retry, failing the pipeline after 10 total attempts.

**Notes:** Reuse the existing 500 error recovery mechanism (chunk shrinking) for verification failures.
