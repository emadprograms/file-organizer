# Wave 3 Summary: Standardize User-Facing Output & Sync Verbosity

## Objective
Clarify the boundary between system telemetry (logging) and user-facing CLI output (Rich console) and sync UI verbosity with the global `verbose` flag.

## Changes

### 1. Infrastructure for Conditional UI
- Created `src/core/ui.py` to provide a centralized `console` instance and a `vprint` helper.
- `vprint` only outputs to the console if the global verbosity flag is enabled.
- Integrated `set_verbosity()` in `src/organize.py` to sync the CLI `--verbose` flag with the UI state.

### 2. Standardized Console Usage
- Audited all `rich.console` usage across `src/`.
- Confirmed that system telemetry is handled by `logger.info()` and not `console.print`.
- Migrated all detailed UI output (tables, trees) to use `vprint`.

### 3. Conditional UI Elements
The following UI elements are now conditional and only appear when `--verbose` is passed:
- **Dry Run Folder Tree**: The hierarchical preview of the output directory structure (`src/processing/organizer/core.py`).
- **Reconciliation Report**: The summary table of input vs. output pages (`src/processing/organizer/reconciliation.py`).
- **Dry Run Summary**: The full visualizer output including the metrics table and resource tree (`src/processing/visualizer.py`).

## Verification
- Verified that `src/core/ui.py` correctly toggles output based on the `_verbose` state.
- Confirmed that all local `Console()` instantiations were removed in favor of the central utility.
- Confirmed that telemetry remains in the logger.
