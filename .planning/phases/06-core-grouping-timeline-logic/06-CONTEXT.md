# Phase 6: Core Grouping & Timeline Logic - Context

**Gathered:** 2026-06-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Overhaul the logic that groups pages into documents and assigns them to resident timelines, ensuring families stay together and documents aren't orphaned or hijacked.

</domain>

<decisions>
## Implementation Decisions

### Large families on Anchor docs (LOGIC-01)
- **D-01:** Keep a safety threshold of 10 names for anchor documents to prevent massive parsing errors from hijacking timelines.

### Date mismatch grouping (LOGIC-04)
- **D-02:** Add an `is_continuation` boolean flag to the LLM extraction schema (Pass 1). The grouping logic will respect this flag to merge undated or mismatching pages that are continuations. 
- **D-03:** The LLM extraction and retry logic for `is_continuation` MUST respect the global rate limits and backoff logic to prevent hammering the API.

### Prefix ID cards (LOGIC-05) & Non-Anchor routing (LOGIC-06)
- **D-04:** Implement **"Verified Residents" Pre-scan:** Before Pass 2 groups any documents, scan all pages for Anchor documents (Contracts, Basic Details, Key Handover). Any name on an Anchor document is officially registered as a Verified Resident.
- **D-05:** Implement **Temporary Routing:** For non-anchor documents (e.g. Notifications), route the document to the named person ONLY if they are a Verified Resident. Otherwise, ignore the unverified name and leave the document in the current active timeline.
- **D-06:** Implement **Retrospective Assignment:** Buffer any early non-anchor documents (like Prefix ID cards) encountered while the timeline is still `UNKNOWN`. When the first Anchor document is found and establishes a timeline, retroactively assign the buffered documents to that newly verified resident.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 6 success criteria
- `.planning/REQUIREMENTS.md` — LOGIC-01 through LOGIC-06 details

### Code Structure
- `src/pipeline.py` — Location of the 2-pass architecture and timeline logic that needs updating
- `src/organizer.py` — Location of `_build_resident_order` and folder generation rules
- `src/schemas.py` — Where `is_continuation` flag will be added

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/schemas.py` defines the `PageClassification` schema that needs extending.
- `pipeline.py` Pass 1.5 (`canonical_mapping`) runs over the whole file before Pass 2. This allows the Verified Residents Pre-scan to be done right after Pass 1.5.

### Established Patterns
- Pass 1 processes pages via ThreadPoolExecutor. Retries for `is_continuation` missing must reuse `self.client.classify_page` error handling to respect the 15 RPM cap.
- Pass 2 iterates sequentially over `raw_pages`.

### Integration Points
- Temporary Routing will replace lines 198-202 in `pipeline.py`.
- Retrospective Assignment will require adding a buffer queue before the main loop starts assigning `documents.append()`.

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

*Phase: 6-Core Grouping & Timeline Logic*
*Context gathered: 2026-06-23*
