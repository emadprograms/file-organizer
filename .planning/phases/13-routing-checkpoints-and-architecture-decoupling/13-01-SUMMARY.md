# Summary: Refactor Routing State Schema and Configuration

## Objective
Refactor the routing state schema and global configuration to support persistence of actual routing results (folder paths) instead of just tracking processed indices, and to allow explicit model selection for the routing process.

## Changes
- **Configuration**: Added `ROUTING_MODEL` constant to `src/core/config.py` with a default value of `google/gemma-4-26b-a4b-it`, supporting environment variable overrides.
- **State Schema**: Refactored `RoutingState` in `src/processing/routing/state.py`:
    - Removed `processed_indices: List[int]`.
    - Added `results: dict[int, str]` to map document indices to their assigned folder paths.
    - Updated `grouping_checksum: str | None` to be optional and persist the checksum active during routing.
    - Updated class docstring for clarity.

## Verification Results
- **Automated Checks**: Verified existence of `ROUTING_MODEL` in `config.py` and `results` dictionary in `state.py` using `Select-String`.
- **Functional Test**: Created and executed a temporary persistence test (`tests/test_routing_state_persistence_tmp.py`) verifying that `RoutingState` can be initialized, updated, saved, and loaded without data loss.

## Outcome
The routing state now correctly tracks the actual results of the routing process, preventing data loss and enabling efficient resumption. The routing model is now configurable via global settings.
