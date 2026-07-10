# Summary: Pipeline Decoupling and Routing Checkpoints (13-02)

## Objectives
- Refactor `Pipeline._group_and_route_documents` to decouple grouping and routing into distinct stages.
- Implement granular checkpointing for the routing stage.
- Add a sanity check using a checksum of grouping results to prevent routing resumption on inconsistent state.

## Changes
### 1. Pipeline Refactoring (`src/processing/pipeline.py`)
- **Decoupled Routing Loop:** Routing is now a separate loop that iterates over the final list of `documents` after all grouping runs have finished.
- **Grouping Checksum:** Implemented a checksum based on the `start_page`, `end_page`, and `category` of all documents to uniquely identify the current grouping state.
- **Routing Checkpoints:** Integrated `RoutingStateManager` using a dedicated `_routing.json` checkpoint file. The state is saved atomically after each individual document is routed.
- **Sanity Check:** Added logic to compare the current grouping checksum with the one stored in `RoutingState`. If they mismatch, the routing state is cleared to ensure consistency.
- **Checkpoint Cleanup:** The pipeline now removes both the grouping run checkpoint and the routing checkpoint upon successful completion of the entire process.

## Verification Results
- **Feature Tests:** Created and verified `tests/test_pipeline_routing.py` which specifically tests routing resumption from checkpoints and the checksum-based restart logic.
- **Regression Tests:** Verified that `tests/test_pipeline.py` continues to pass.
- **Test Result:** All tests in `tests/test_pipeline_routing.py` and `tests/test_pipeline.py` passed.
