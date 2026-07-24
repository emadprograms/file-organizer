# Phase 25: Extract Presentation Logic from `core/` - Research

**Date:** 2026-07-24  
**Status:** Completed  
**Domain:** Codebase Architecture / Refactoring (ARCH-01)

## Executive Summary

Phase 25 refactors `src/core/ui.py` into `src/presentation/ui.py`. The `core/` package is reserved strictly for pure data contracts (models, schemas, exceptions, config, indexing). Presentation logic (`console`, `_verbose`, `set_verbosity`, `vprint`) belongs in `src/presentation/`.

This refactor is purely structural; no functionality or runtime behavior is altered.

---

## Code Analysis & Inspection Results

### Source Module: `src/core/ui.py`
- **Imports:** `typing.Any`, `rich.console.Console`, `logging`
- **Globals:** `console = Console()`, `_verbose = False`, `logger = logging.getLogger(f"file_organizer.{__name__}")`
- **Functions:**
  - `set_verbosity(verbose: bool) -> None`: Sets global `_verbose` flag.
  - `vprint(*args: Any, **kwargs: Any) -> None`: Conditional print using Rich `console`.

### Dependencies & Circular Import Assessment
- `ui.py` does not import any other modules from `src/core/` or `src/`.
- Moving `src/core/ui.py` to `src/presentation/ui.py` introduces zero circular dependency risk.
- `src/presentation/__init__.py` should exist so `src.presentation.ui` can be cleanly imported.

---

## Import Site Inventory

Every reference to `src.core.ui` / `core.ui` across `src/` and `tests/`:

| File | Line | Current Code | Target Code |
|------|------|--------------|-------------|
| `src/main.py` | L17 | `from src.core.ui import set_verbosity` | `from src.presentation.ui import set_verbosity` |
| `src/pipeline/visualizer.py` | L5 | `from src.core.ui import vprint` | `from src.presentation.ui import vprint` |
| `src/timeline/core.py` | L271 | `from src.core.ui import vprint` | `from src.presentation.ui import vprint` |
| `src/timeline/reconciliation.py` | L62 | `from src.core.ui import vprint` | `from src.presentation.ui import vprint` |
| `tests/test_core_ui.py` (rename to `tests/test_presentation_ui.py`) | L4, L10, L15 | `from src.core.ui import console, set_verbosity, vprint`, `from src.core.ui import _verbose` | `from src.presentation.ui import console, set_verbosity, vprint`, `from src.presentation.ui import _verbose` |
| `tests/test_pipeline_visualizer.py` | L4 | `from src.core.ui import set_verbosity` | `from src.presentation.ui import set_verbosity` |
| `tests/test_utils_logger.py` | L140 | `"src.core.ui"` | `"src.presentation.ui"` |
| `architecture_and_directory_map.md` | L208 | `src/core/ui.py` | `src/presentation/ui.py` |

---

## Verification & Test Plan

1. Create `src/presentation/ui.py` and `src/presentation/__init__.py`.
2. Remove `src/core/ui.py`.
3. Update imports across all 7 identified files.
4. Move `tests/test_core_ui.py` to `tests/test_presentation_ui.py`.
5. Execute `pytest` and verify all 262 tests pass with 0 failures.
