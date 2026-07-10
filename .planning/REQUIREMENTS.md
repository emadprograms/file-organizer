# Requirements: v1.3 Routing Decoupling & Checkpointing

## Objective
Decouple the routing step from grouping to improve pipeline resilience, enable independent LLM model configuration, and support resuming routing without re-running grouping. Also, implement conditional LLM folder routing.

## Constraints
- Do not break the existing end-to-end functionality.
- Existing tests should pass, or be updated if the architecture changes.
- Ensure backwards compatibility with `.json` checkpoints from prior phases.

## Epic: Architecture (ARCH)
- [ ] **ARCH-01**: Refactor `src/processing/pipeline.py` to separate `group_documents` and `route_documents` into distinct steps.

## Epic: Resilience (RES)
- [ ] **RES-01**: Implement a dedicated `routing_checkpoint.json` mechanism in the orchestrator so routing can be resumed on failure.

## Epic: Configuration (CFG)
- [ ] **CFG-01**: Update `LLMClient` initialization and usage to allow separate models for grouping and routing (e.g. `routing_model` parameter).

## Epic: Routing (ROUT)
- [ ] **ROUT-01**: Implement Conditional LLM Folder Routing and Folder Renaming (Phase 11 backlog).
