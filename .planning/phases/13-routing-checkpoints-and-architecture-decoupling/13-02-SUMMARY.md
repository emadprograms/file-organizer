# Summary: Task 13-02 - Pipeline Decoupling and Routing Fix

## Objective
Decouple the pipeline architecture and fix the routing resumption bug by restoring state into document objects.

## Changes
- **Pipeline Initialization**: Updated `Pipeline.__init__` to explicitly track `routing_model`, defaulting to `src.core.config.ROUTING_MODEL`.
- **Architectural Decoupling**: 
    - Extracted grouping logic into `_group_documents`.
    - Extracted routing logic into `_route_documents`.
    - Refactored `_group_and_route_documents` to orchestrate these two private methods.
- **Routing Resumption Fix**:
    - Replaced `processed_indices` with `state.results` for tracking progress.
    - Implemented the "Skip-and-Forget" fix: documents are now restored with their `folder_path` from `state.results` upon resumption.
- **Robustness**:
    - Implemented a pre-route sanity check that resets `state.results` if the grouping checksum has changed, preventing incorrect routing assignments.
- **Model Propagation**:
    - Ensured `route_document` is called with the explicitly tracked `self.routing_model`.

## Verification Results
- `self.routing_model` is correctly initialized and used.
- `_group_documents` and `_route_documents` are implemented and called by the main pipeline method.
- Resumption logic restores `folder_path` from `state.results`.
- Sanity check for grouping checksum is implemented.

## Artifacts
- Modified: `src/processing/pipeline.py`
