# Phase 13: Routing Checkpoints & Architecture Decoupling - Research

**Researched:** 2026-07-11
**Domain:** Pipeline Orchestration & State Persistence
**Confidence:** HIGH

## Summary

This research addresses a critical failure in the document routing process where previously computed routing results (`folder_path`) are lost upon pipeline resumption. Currently, `RoutingState` only tracks *which* indices were processed, but not *what* the result was. When the `Pipeline` resumes, it skips processed indices, leaving their `folder_path` as `None` in the resulting `DocumentGroup` objects.

Additionally, the pipeline suffers from "Implicit Model Propagation," where the routing model is not explicitly specified by the orchestrator, leading to reliance on `LLMClient` defaults which may be inconsistent with routing requirements.

**Primary recommendation:** Transition `RoutingState` from an index-tracking list to a result-mapping dictionary and refactor the `Pipeline` to decouple grouping and routing into two distinct, checkpointed stages.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Implement granular checkpoints saved after each document group is routed.
- **D-02:** Use a modular, functional approach consistent with the Grouping implementation.
- **D-03:** Use a dynamic parameter for the routing model passed to routing functions.
- **D-04:** Perform a "sanity check" (checksum) when resuming to ensure grouping state is consistent.

### the agent's Discretion
- Specific structure of `RoutingStateManager`.
- Exact a-priori sanity check mechanism.

### Deferred Ideas (OUT OF SCOPE)
- None.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Routing Logic | Backend (Routing) | — | `router.py` owns the logic of picking a folder. |
| State Persistence | Backend (Routing) | — | `state.py` owns how routing progress is saved to disk. |
| Pipeline Orchestration | Backend (Pipeline) | — | `pipeline.py` coordinates the flow between grouping and routing. |
| Model Configuration | Core (Config) | Pipeline | Config defines available models; Pipeline selects the one for routing. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | v2.x | State schemas | Consistent with project-wide data validation. |
| `atomic_write` | Project Util | Persistence | Ensures checkpoints aren't corrupted during crashes. |

## Architecture Patterns

### Recommended Project Structure
The existing structure is sufficient, but the logic within `Pipeline` must be decoupled.

### Pattern: Functional Decoupling (Resumption-Ready)
The `Pipeline` should not contain business logic. It should orchestrate standalone functions.

**Current (Tightly Coupled):**
`Pipeline._group_and_route_documents` does everything in one monolithic method.

**Proposed (Decoupled):**
1. `Pipeline._group_documents(...)` $ightarrow$ returns `list[DocumentGroup]`
2. `Pipeline._route_documents(documents, ...)` $ightarrow$ modifies `documents` in place and returns them.

### Anti-Patterns to Avoid
- **Index-only Tracking:** Tracking `processed_indices` without storing the corresponding results is the root cause of the current data loss.
- **Default Model Reliance:** Calling `route_document(doc, client)` without specifying the `model` parameter.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| State Persistence | Custom JSON write | `RoutingStateManager` | Handles backups and atomic replacements. |
| Checksumming | Custom loop | `hashlib.sha256` | Standard, collision-resistant. |

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `_routing.json` state files | **Schema Migration**: Existing state files using `processed_indices` will be incompatible with the new `results` dict. These should be treated as stale and cleared (which the checksum check already handles). |
| Secrets/env vars | `OPENROUTER_MODEL` etc. | Ensure `Pipeline` can access these via `config.py`. |

## Common Pitfalls

### Pitfall 1: The "Skip-and-Forget" Bug
**What goes wrong:** The loop uses `if i in state.processed_indices: continue`.
**Why it happens:** It assumes the `doc` object already has the result, but `doc` is reconstructed from a checkpoint or created fresh, while the result was only stored in the state manager's memory/file.
**How to avoid:** Always restore the state value into the object before continuing.

### Pitfall 2: Model Drift
**What goes wrong:** Routing behavior changes between runs because the default model in `LLMClient` was updated.
**Why it happens:** Lack of explicit model passing.
**How to avoid:** Pass the model explicitly from `Pipeline` $ightarrow$ `route_document` $ightarrow$ `LLMClient`.

## Code Examples

### Corrected Routing Loop
```typescript
# Proposed Python Logic in Pipeline._route_documents
for i, doc in enumerate(documents):
    # 1. Restore from state if already processed
    if i in state.results:
        doc.folder_path = state.results[i]
        # Optional: restore is_direct_routed if added to schema
        continue
    
    # 2. Explicitly pass the routing model
    folder, is_direct = route_document(doc, self.client, model=self.routing_model)
    
    # 3. Update object and state
    doc.folder_path = folder
    doc.is_direct_routed = is_direct
    state.results[i] = folder
    
    if routing_state_manager:
        routing_state_manager.save_state(state)
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `is_direct_routed` is less critical than `folder_path` | Summary | If it is critical, the `results` dict must store a tuple or object instead of just a string. |

## Open Questions (RESOLVED)

1. **Where should the `routing_model` default come from?**
   - (RESOLVED): Define a `ROUTING_MODEL` constant in `src/core/config.py` and allow `Pipeline` to override it in `__init__`.

## Validation Architecture

### Test Framework
- Framework: `pytest`
- Quick run: `pytest tests/test_routing_state.py`

### Phase Requirements $ightarrow$ Test Map
| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| RES-01 | Resume routing without data loss | E2E | `pytest tests/test_pipeline_routing.py::test_resumption_persistence` |
| CFG-01 | Explicit model propagation | Unit | `pytest tests/test_routing.py::test_model_parameter_passed` |

### Wave 0 Gaps
- [ ] `tests/test_pipeline_routing.py` needs a specific test case for "Interrupt $ightarrow$ Resume $ightarrow$ Verify Folders".

## Security Domain

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | Pydantic validation of `RoutingState` during `load_state`. |

## Sources

### Primary (HIGH confidence)
- `src/processing/routing/state.py` - analyzed current state schema.
- `src/processing/pipeline.py` - analyzed routing loop and identified data loss bug.
- `src/processing/routing/router.py` - verified `model` parameter support.
- `src/core/schemas.py` - verified `DocumentGroup` fields.
