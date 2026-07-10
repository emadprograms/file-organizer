# Phase 13: Routing Checkpoints & Architecture Decoupling - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Decouple the routing step from grouping to improve pipeline resilience, enable independent LLM model configuration, and support resuming routing on failure without re-running the entire grouping process.

</domain>

<decisions>
## Implementation Decisions

### Checkpoint Granularity
- **D-01:** Implement granular checkpoints saved after each document group is routed. This ensures maximum resilience and minimizes re-work on failure.

### Architecture Decoupling
- **D-02:** Use a modular, functional approach consistent with the Grouping implementation. Routing logic will remain as standalone functions in the `src/processing/routing/` module, orchestrated by the `Pipeline` class.

### LLM Model Configuration
- **D-03:** Use a dynamic parameter for the routing model. The model name will be passed as a parameter to the routing functions, allowing the pipeline to potentially switch models dynamically or handle different configurations per call.

### Resumption Logic
- **D-04:** Perform a "sanity check" when resuming from a routing checkpoint to ensure the grouping state (the input to routing) is still consistent before continuing.

### Claude's Discretion
The specific structure of the `RoutingStateManager` and the exact a-priori sanity check mechanism are left to Claude's discretion during planning, provided they adhere to the decisions above.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Routing Configuration & Implementation
- `.planning/phases/11-conditional-llm-folder-routing-and-folder-renaming/11-CONTEXT.md` — Defines the routing constraints and requirements.
- `.planning/phases/12-finalize-conditional-llm-folder-routing-and-folder-renaming/12-CONTEXT.md` — Final polish decisions for routing.
- `src/processing/routing/config.py` — Source of truth for Arabic folder names.
- `src/processing/routing/router.py` — Current routing logic.

### Pipeline & Grouping Reference
- `src/processing/pipeline.py` — The orchestrator that needs decoupling.
- `src/processing/grouping/core.py` — The model for the functional decoupling and shrink logic.
- `src/processing/grouping/state.py` — The model for state management and persistence.

### Project Guidelines
- `.planning/PROJECT.md` — Project-level goals.
- `.planning/REQUIREMENTS.md` — Milestone v1.3 objectives (ARCH, RES, CFG).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `GroupingStateManager` in `src/processing/grouping/state.py`: This is the blueprint for the new `RoutingStateManager`.
- `atomic_write` in `src/fs_utils.py`: Must be used for all checkpoint saves.

### Established Patterns
- **Functional Decoupling**: The pipeline orchestrates standalone functions in `grouping.core` rather than using internal class methods.
- **State-Based Resumption**: Use of state managers to track processed indices and persist data to disk.

### Integration Points
- `Pipeline._group_and_route_documents`: This method must be refactored to split grouping and routing into two distinct, checkpointed stages.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly prefers a "sanity check" on resumption to avoid routing documents based on stale or corrupted grouping results.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-Routing Checkpoints & Architecture Decoupling*
*Context gathered: 2026-07-10*
