---
wave: 1
depends_on: []
files_modified:
  - src/presentation/__init__.py
  - src/presentation/ui.py
  - src/core/ui.py
  - src/main.py
  - src/pipeline/visualizer.py
  - src/timeline/core.py
  - src/timeline/reconciliation.py
  - tests/test_core_ui.py
  - tests/test_presentation_ui.py
  - tests/test_pipeline_visualizer.py
  - tests/test_utils_logger.py
  - architecture_and_directory_map.md
autonomous: true
---

# Phase 25: Extract Presentation Logic from `core/` Plan

## Goal
Relocate `src/core/ui.py` to `src/presentation/ui.py` to ensure `core/` contains only pure data contracts, config, and models. Update all dependent import sites and test suites.

## Requirements Covered
- **ARCH-01**: Extract Presentation Logic from `core/`

<threat_model>
ASVS Level: 1
Blocking Threshold: High
Threats:
- Broken import references causing runtime `ImportError` or `ModuleNotFoundError`.
- Mismatched verbosity state if dual singletons or relative imports are duplicated.
- Broken test assertions when inspecting logger hierarchical naming (`test_utils_logger.py`).
Mitigations:
- Verify all import sites across `src/` and `tests/` via full grep audit.
- Rename test file to `test_presentation_ui.py` and maintain 1:1 parity of exported public symbols (`console`, `_verbose`, `set_verbosity`, `vprint`).
</threat_model>

## Tasks

### Wave 1: Relocate Presentation UI Module

<task>
<description>Move ui.py to src/presentation/ and remove src/core/ui.py</description>
<action>
1. Create `src/presentation/__init__.py` if missing.
2. Create `src/presentation/ui.py` containing the exact code from `src/core/ui.py` (`console`, `_verbose`, `set_verbosity`, `vprint`, and `logger`).
3. Delete `src/core/ui.py`.
</action>
<read_first>
- src/core/ui.py
</read_first>
<acceptance_criteria>
- `src/presentation/ui.py` exists and exports `console`, `_verbose`, `set_verbosity`, and `vprint`.
- `src/core/ui.py` no longer exists on disk.
</acceptance_criteria>
</task>

### Wave 2: Update Import Sites and Test Suite

<task>
<description>Update imports in src and tests, rename test_core_ui.py to test_presentation_ui.py</description>
<action>
1. Update `src/main.py`: `from src.core.ui import set_verbosity` -> `from src.presentation.ui import set_verbosity`.
2. Update `src/pipeline/visualizer.py`: `from src.core.ui import vprint` -> `from src.presentation.ui import vprint`.
3. Update `src/timeline/core.py`: `from src.core.ui import vprint` -> `from src.presentation.ui import vprint`.
4. Update `src/timeline/reconciliation.py`: `from src.core.ui import vprint` -> `from src.presentation.ui import vprint`.
5. Rename `tests/test_core_ui.py` to `tests/test_presentation_ui.py` and update its imports from `src.core.ui` to `src.presentation.ui`.
6. Update `tests/test_pipeline_visualizer.py`: `from src.core.ui import set_verbosity` -> `from src.presentation.ui import set_verbosity`.
7. Update `tests/test_utils_logger.py`: replace `"src.core.ui"` with `"src.presentation.ui"` in `modules_to_check`.
8. Update `architecture_and_directory_map.md` to reference `src/presentation/ui.py` under Presentation section.
</action>
<read_first>
- src/main.py
- src/pipeline/visualizer.py
- src/timeline/core.py
- src/timeline/reconciliation.py
- tests/test_core_ui.py
- tests/test_pipeline_visualizer.py
- tests/test_utils_logger.py
- architecture_and_directory_map.md
</read_first>
<acceptance_criteria>
- Grep search for `src.core.ui` or `core.ui` in `src/` and `tests/` returns zero active code import matches.
- `tests/test_presentation_ui.py` exists and `tests/test_core_ui.py` is removed.
- `tests/test_utils_logger.py` passes logger check on `src.presentation.ui`.
</acceptance_criteria>
</task>

### Wave 3: Verification Loop

<task>
<description>Run pytest verification suite</description>
<action>
Execute `pytest` across the test suite to verify 100% test pass rate (262 tests passing).
</action>
<read_first>
- tests/test_presentation_ui.py
</read_first>
<acceptance_criteria>
- `pytest` exits with code 0 and all tests pass.
</acceptance_criteria>
</task>
