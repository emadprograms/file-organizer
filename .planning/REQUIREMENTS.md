---
gsd_version: "1.0"
milestone: v4.0
milestone_name: Architectural Cleanup
---

# Requirements: v4.0 Architectural Cleanup

## Goal

Surgical cleanup of module boundaries, naming, and import hygiene without adding features or changing behavior. Every change is independently testable and committable.

## Requirements

### ARCH-01: Extract Presentation Logic from `core/`

**Priority:** High  
**Status:** Pending

Move `src/core/ui.py` out of `src/core/` to a standalone `src/ui.py` module (or `src/presentation/ui.py`).

`core/` should only contain pure data contracts (models, schemas, exceptions, config). Presentation logic (`vprint`, `set_verbosity`, `console`) violates this boundary.

**Acceptance Criteria:**
- [ ] `src/core/ui.py` no longer exists
- [ ] New location exports the same public API (`console`, `set_verbosity`, `vprint`)
- [ ] All imports updated across `src/` and `tests/`
- [ ] All 262 tests pass

**Affected files (imports to update):**
- `src/main.py`
- `src/pipeline/visualizer.py`
- `src/timeline/core.py`
- `src/timeline/reconciliation.py`
- `tests/test_core_ui.py`
- `tests/test_pipeline_visualizer.py`

---

### ARCH-02: Rename `fs_ui/` to `watcher/`

**Priority:** High  
**Status:** Pending

Rename `src/fs_ui/` to `src/watcher/` to accurately describe what the package does (file watching, process locking, event-driven orchestration).

**Acceptance Criteria:**
- [ ] `src/fs_ui/` directory no longer exists
- [ ] `src/watcher/` contains `orchestrator.py`, `lock.py`, `__init__.py`
- [ ] All imports updated across `src/` and `tests/`
- [ ] All 262 tests pass

**Affected files (imports to update):**
- `src/main.py` (2 imports)
- `tests/test_e2e_fs_ui.py`
- `tests/test_fs_ui_append_mock.py`
- `tests/test_fs_ui_lock.py`
- `tests/test_fs_ui_orchestrator.py`
- `tests/test_root_main_append_mode.py`

---

### ARCH-03: Disambiguate Reconciliation Modules

**Priority:** Medium  
**Status:** Pending

Rename `src/timeline/reconciliation.py` to `src/timeline/page_integrity.py` to distinguish it from `src/reconcile/core.py` (tenant reconciliation CLI tool).

Currently both modules relate to "reconciliation" but serve completely different purposes:
- `timeline/reconciliation.py`: Verifies page completeness after PDF generation
- `reconcile/core.py`: CLI tool to retroactively re-attribute documents when tenant YAML changes

**Acceptance Criteria:**
- [ ] `src/timeline/reconciliation.py` no longer exists
- [ ] `src/timeline/page_integrity.py` exports `run_reconciliation` (same public API)
- [ ] `src/timeline/__init__.py` updated
- [ ] All imports and mock patch targets updated
- [ ] All 262 tests pass

**Affected files:**
- `src/timeline/__init__.py`
- `src/timeline/reconciliation.py` → `src/timeline/page_integrity.py`
- `tests/test_timeline_reconciliation.py` (patch target)

---

### ARCH-04: Clean Up `main.py` Dead Imports

**Priority:** Low  
**Status:** Pending

After the runner extraction refactor, `main.py` still imports `fitz` and `json` at the module level even though it no longer uses them directly (those are now in `runner.py`).

**Acceptance Criteria:**
- [ ] `import fitz` removed from `src/main.py`
- [ ] `import json` removed from `src/main.py` (if unused)
- [ ] No other module-level imports are dead
- [ ] All 262 tests pass

---

### ARCH-05: Audit Test Mock Patch Targets

**Priority:** Low  
**Status:** Pending

Ensure all test files patch mock targets at the **import site** (where the name is looked up at runtime), not at the definition site. The runner refactor exposed several cases where patches targeted `src.main.*` when the function was actually called from `src.pipeline.runner` or `src.fs_ui.orchestrator`.

**Acceptance Criteria:**
- [ ] All `@patch()` targets verified against actual import chains
- [ ] No patches target modules where the symbol isn't actually looked up
- [ ] All 262 tests pass
