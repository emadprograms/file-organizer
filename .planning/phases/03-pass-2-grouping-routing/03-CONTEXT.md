# Phase 3: Pass 2 — Grouping & Routing - Context

**Gathered:** 2026-07-04
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase takes the cleaned page sequence (from Pass 1, where every page has a canonical tenant and date) and divides it into multi-page logical documents. It implements boundary detection with overlapping chunks, programmatic verification of LLM grouping, document routing, and physical PDF splitting using PyMuPDF.

</domain>

<decisions>
## Implementation Decisions

### Overlap Merge Resolution
- **D-01:** Trust the chunk where the document started (Chunk 1) for resolving disagreements on the overlap page — it has the context of the document's origin.

### Multi-match Routing Fallback
- **D-02:** If the LLM fails to pick a valid folder for ambiguous documents (like letters or forms), retry the LLM call once with stricter constraints. If it still fails, fallback to the generic "others" sub-folder.

### Verification Failure Handling
- **D-03:** If the LLM returns valid JSON but repeatedly fails the programmatic gap/overlap verification, treat it like a 500 error: shrink the chunk size and retry, failing the pipeline after 10 total attempts.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/REQUIREMENTS.md` - Core requirements for GRP-01 through GRP-13.
- `.planning/PROJECT.md` - Key decisions (Subject/content shift as ONLY boundary signal, hardcoded routing rules).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/processing/split.py` - Contains PDF extraction and compression tools (`extract_pdf_segment`, `compress_pdf`).
- `src/processing/organizer.py` - Contains `FileOrganizer` framework that needs to be adapted or extended.
- `src/core/schemas.py` - Contains data models like `DocumentGroup`.

### Established Patterns
- Centralized LLM client usage for all API calls (from Phase 1).
- Rate limiting and retry logic handling 500s and 429s centrally.

### Integration Points
- This phase consumes the output of Pass 1 (where pages have been cleaned) and produces the final physical PDF documents and folder structure.

</code_context>

<specifics>
## Specific Ideas

- The boundary detection should only trigger on subject/topic shift and context/content shift, ignoring date and sender changes as boundaries.

</specifics>

<deferred>
## Deferred Ideas

None

</deferred>

---

*Phase: 3-Pass 2 — Grouping & Routing*
*Context gathered: 2026-07-04*
