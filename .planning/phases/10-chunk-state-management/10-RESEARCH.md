# Phase 10: Chunk State Management - Research

**Researched:** 2026-07-09
**Domain:** State Persistence and Resilient Chunking for Document Grouping
**Confidence:** HIGH

## Summary

Phase 10 focuses on making the document grouping process resilient to "Hard Halts" (introduced in Phase 09) and improving the stability of chunked processing. The current implementation in `src/processing/grouping/core.py` uses a basic shrinking mechanism that is not persisted to disk and lacks a strict definition of failure based on provider rotation.

The primary goal is to transition from a volatile, index-based shrinking system to a persisted state machine that can resume after a crash, dynamically adjust chunk sizes based on full provider rotation failures, and merge overlapping chunks using an "Anchor Page" strategy validated by the LLM.

**Primary recommendation:** Implement a dedicated `GroupingStateManager` to handle atomic JSON checkpoints and refactor `process_with_shrink` to use a state-driven loop instead of local variables for tracking progress and failures.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Chunk Size Sequence:** The system will process pages in chunks of **5, 3, then 2**.
- **Failure Definition:** One "fail" is defined as a **full rotation through the provider cycle** (Gemini $ightarrow$ Secondary $ightarrow$ Gemini $ightarrow$ Secondary).
- **Shrink Trigger:** If a full provider rotation fails, reduce chunk size (5 $ightarrow$ 3 $ightarrow$ 2).
- **Reset Logic:** Upon success, reset chunk size index to **0** (size 5).
- **Persistent Failure State:** `current_chunk_size_index` and `failure_count` must be persisted to disk to survive "Hard Halts".
- **Checkpointing Frequency:** Save a checkpoint **after every single LLM response**.
- **Halt Behavior:** When chunk size 2 fails, trigger a graceful halt and save state.
- **Overlap Merging:** Use a 1-page overlap (anchor page) and rely on the LLM's grouping decision for that page to bridge chunks.

### the agent's Discretion
- **State File:** Use a lightweight JSON file in the phase directory to track state independently of grouped data.
- **Atomic Checkpoints:** Ensure the checkpointing process is atomic.

### Deferred Ideas (OUT OF SCOPE)
None.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| State Persistence | API / Backend | — | Logic for saving/loading state resides in the grouping core. |
| Dynamic Chunking | API / Backend | — | Control loop for chunk size resides in `process_with_shrink`. |
| Overlap Merging | API / Backend | — | Utility logic to merge results from separate LLM calls. |
| Failure Detection | API / Backend | LLM Client | Logic depends on `LLMClient`'s rotation results. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | ^2.0 | State Schema | For structured validation of the state file. |
| JSON/OS | Stdlib | Persistence | Simple, human-readable, and atomic via temp-file swap. |

## Analysis of Current Implementation

### Current Grouping Logic (`src/processing/grouping/core.py`)
- **Loop Structure:** Uses a `while current_page_index < len(pages)` loop.
- **Chunking:** Calculates `end_index` based on `CHUNK_SIZES[chunk_size_idx]`.
- **Failure Handling:** 
    - Uses `consecutive_failures` and `total_failures` (local variables).
    - Shrinks chunk size when `consecutive_failures >= MAX_CONSECUTIVE_FAILURES`.
- **Overlap:** Uses `overlap = 1` to move the `current_page_index` back by one page.
- **Merging:** Calls `merge_chunks` in `utils.py`, which checks if the `overlap_page_idx` is present in both the last group of Chunk 1 and first group of Chunk 2.

### Identified Gaps
1. **Volatile State:** If the process crashes (Hard Halt), all progress in `current_page_index`, `chunk_size_idx`, and `failure_count` is lost.
2. **Vague Failure Definition:** Currently shrinks on `MAX_CONSECUTIVE_FAILURES` regardless of whether a provider rotation occurred.
3. **Lack of Reset:** `chunk_size_idx` never resets to 0 upon success.
4. **Mathematical Merge Risk:** The current `merge_chunks` is a simple index check. While it uses LLM-generated groups, it doesn't explicitly verify "boundary validation" as requested.

## Proposed Implementation Details

### 1. State Persistence Integration
A `GroupingStateManager` should be introduced to encapsulate state operations.

**Proposed State Structure (`grouping_state.json`):**
```json
{
  "current_page_index": 12,
  "chunk_size_index": 1,
  "failure_count": 0,
  "processed_groups": [
    { "start_page": 0, "end_page": 4, ... },
    { "start_page": 5, "end_page": 11, ... }
  ],
  "last_updated": "2026-07-09T12:00:00Z"
}
```

**Integration Points in `process_with_shrink`:**
- **Initialization:** Load state from file if it exists; otherwise, initialize to defaults.
- **After `_process_chunk` success:** 
    - Append `chunk_groups` to `processed_groups`.
    - Update `current_page_index`.
    - Reset `chunk_size_index` to 0.
    - **Trigger Atomic Checkpoint.**
- **After Provider Rotation Failure:**
    - Increment `failure_count`.
    - If rotation complete $ightarrow$ increment `chunk_size_index`.
    - **Trigger Atomic Checkpoint.**

### 2. Anchor Page Merging Logic
To avoid "mathematical" merging and ensure "LLM-validated" boundaries:

**The Process:**
1. **Overlap Definition:** Chunk $N$ ends at Page $P$. Chunk $N+1$ starts at Page $P$. Page $P$ is the **Anchor Page**.
2. **LLM Validation:**
    - In Chunk $N$, the LLM determines if Page $P$ is the *end* of a document or *continues* into the next.
    - In Chunk $N+1$, the LLM determines if Page $P$ is the *start* of a document or a *continuation* from the previous.
3. **Merge Condition:**
    - If the group containing Page $P$ in Chunk $N$ and the group containing Page $P$ in Chunk $N+1$ are both processed as part of a "document group" (not just a single page fragment), they are merged.
    - The merge is only performed if the LLM's `reason` for Page $P$ in both chunks suggests the same document context.

**Proposed Code Change for `merge_chunks`:**
Instead of just checking `contains_page`, the logic should:
- Identify the `group_N` containing `overlap_page_idx`.
- Identify the `group_N+1` containing `overlap_page_idx`.
- Merge if both exist.
- The `DocumentGroup` attributes (tenant, category) from `group_N` are preserved as the primary source of truth.

### 3. Dynamic Chunking & Rotation Logic
The failure logic must be tied to the `LLMClient`'s rotation.

**Logic Flow:**
- Call `_process_chunk`.
- If it fails $ightarrow$ catch `LLMFailureError` (or the specific rotation failure).
- Track if the `LLMClient` has completed a full cycle (Gemini $ightarrow$ Sec $ightarrow$ Gemini $ightarrow$ Sec).
- Only when the cycle is complete, increment the `chunk_size_index`.
- If `chunk_size_index` reaches the end of `[5, 3, 2]`, raise a `GracefulHaltException`.

## Requirement Mapping

| Req ID | Behavior | Implementation Change |
|--------|----------|------------------------|
| **GRP-01** | Dynamic Chunking (5, 3, 2) | Update `CHUNK_SIZES` to `[5, 3, 2]`. Implement `chunk_size_idx` reset on success and increment on full rotation failure. |
| **GRP-02** | State Persistence | Create `GroupingStateManager`. Add `save_state()` calls after every LLM response and failure update. |
| **GRP-03** | Overlap Merging (Anchor Page) | Refactor `merge_chunks` to explicitly use the overlap page as an anchor for LLM-validated boundaries. |
| **GRP-04** | Graceful Halt | Add check: if `chunk_size_idx == len(CHUNK_SIZES) - 1` and failure occurs, save final state and exit cleanly. |

## Risks and Edge Cases

| Risk | Impact | Mitigation |
|------|--------|------------|
| **State File Corruption** | Pipeline cannot resume or resumes from wrong page. | Use atomic writes (write to `.tmp` then rename). Implement a simple JSON schema validation on load. |
| **Empty/Malformed Pages** | LLM fails to find boundaries for the anchor page. | Treat "no group found" for anchor page as a boundary (no merge). |
| **Infinite Shrink Loop** | System keeps failing even at size 2. | Strict `GracefulHalt` when size 2 fails. |
| **State/Data Desync** | `processed_groups` in state file differ from actual result. | Ensure `processed_groups` is updated only after `verify_groups` passes. |

## Open Questions (RESOLVED)

1. **State File Location:** Should the state file be in the document's specific processing folder or a global phase state folder? 
   - *Resolution:* Per-document state file to allow parallel processing of multiple documents in the future.
2. **Rotation Tracking:** How does `process_with_shrink` know when a *full* rotation has occurred if the rotation logic is hidden inside `LLMClient`?
   - *Resolution:* `LLMClient` should return a flag or a custom exception (e.g., `RotationExhaustedError`) when a full cycle fails.

## Validation Architecture

### Test Framework
- **Framework:** `pytest`
- **Focus:** Mocking `LLMClient` to simulate failures and verifying that the `grouping_state.json` is updated correctly.

### Phase Requirements $ightarrow$ Test Map
| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| GRP-01 | Chunk size shrinks 5 $ightarrow$ 3 $ightarrow$ 2 | unit | `pytest tests/test_grouping.py::test_shrink_logic` |
| GRP-02 | Resume from state file | integration | `pytest tests/test_grouping.py::test_resume_from_state` |
| GRP-03 | Merge on anchor page | unit | `pytest tests/test_grouping.py::test_anchor_merge` |
| GRP-04 | Halt at size 2 failure | unit | `pytest tests/test_grouping.py::test_graceful_halt` |
