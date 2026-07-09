# Phase 10: Chunk State Management - Context

**Gathered:** 2026-07-09
**Status:** Ready for planning

<domain>
## Phase Boundary
The goal of this phase is to implement a resilient chunking and state management system for document grouping. The system must dynamically adjust chunk sizes upon failure, persist its progress (including failure state) to disk to survive "Hard Halts" from Phase 09, and ensure that the merging of overlapping chunks is done based on LLM-validated boundaries rather than mathematical indices.

</domain>

<decisions>
## Implementation Decisions

### 1. Dynamic Chunking & Failure Logic
- **Chunk Size Sequence:** The system will process pages in chunks of **5, 3, then 2**.
- **Failure Definition:** One "fail" is defined as a **full rotation through the provider cycle** (Gemini $ightarrow$ Secondary $ightarrow$ Gemini $ightarrow$ Secondary).
- **Shrink Trigger:** If a full provider rotation fails (e.g., due to 500 errors or persistent validation failures), the system reduces the chunk size to the next step in the sequence (5 $ightarrow$ 3 $ightarrow$ 2).
- **Reset Logic:** Upon successfully processing a chunk, the chunk size index is reset to **0** (back to size 5).

### 2. State Persistence & Resume
- **Persistent Failure State:** To survive the "Hard Halts" implemented in Phase 09, the current chunk size index and consecutive failure count must be persisted to disk (e.g., in a `state.json` or within the phase checkpoint).
- **Checkpointing Frequency:** A checkpoint MUST be saved **after every single LLM response**. This prevents the system from restarting from the top and ensures it resumes from the exact point of failure.
- **Halt Behavior:** When the final chunk size (2) is exhausted and fails, the system triggers a graceful halt, saving the final state checkpoint and exiting.

### 3. Overlap Merging Logic (The "Anchor" Page)
- **Mechanism:** The system uses a sliding window with a 1-page overlap (e.g., Chunk 1: Pages 1-5; Chunk 2: Pages 5-9).
- **Merge Validation:** Merging is validated by the LLM's grouping decisions for the overlap page (Page 5). If the LLM identifies Page 5 as being part of a group that continues into the next chunk, the chunks are merged.
- **Boundary Respect:** The system must not merge chunks mathematically; it must rely on the LLM's explicit grouping response for the overlapping anchor page to bridge the two chunks.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & Requirements
- `.planning/ROADMAP.md` — Phase 10 success criteria.
- `.planning/REQUIREMENTS.md` — Requirements GRP-01, GRP-02, GRP-03, GRP-04.

### Prior Phase Context
- `.planning/phases/09-rate-limiting-router-safety-net/09-CONTEXT.md` — Defines the "Hard Halt" and provider rotation logic that Phase 10 must integrate with.

### Existing Implementation
- `src/processing/grouping/core.py` — Current grouping and shrink logic.
- `src/core/schemas.py` — Grouping response schemas.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LLMClient` rotation logic from Phase 09 is the foundation for the "full rotation" failure definition.
- Existing `process_with_shrink` infrastructure in `src/processing/grouping/core.py` will be refactored to support persistence and the updated failure cycle.

### Integration Points
- The state persistence must integrate with the overall pipeline's checkpointing system to ensure consistency.
- The "Hard Halt" exception from Phase 09 must be caught by the orchestrator to trigger the final state save.

</code_context>

<specifics>
## Specific Ideas
- **State File:** Consider using a lightweight JSON file in the phase directory to track the `current_chunk_size_index` and `failure_count` independently of the large grouped data.
- **Atomic Checkpoints:** Ensure the checkpointing process is atomic to prevent corruption during a hard halt.

</specifics>

<deferred>
## Deferred Ideas
None.

</deferred>

---
*Phase: 10-chunk-state-management*
*Context gathered: 2026-07-09*
