---
wave: 1
depends_on: []
files_modified:
  - "src/main.py"
  - "src/core/cache.py"
  - "src/core/config.py"
  - "src/core/schemas.py"
  - "src/core/utils.py"
  - "src/llm/llm.py"
  - "src/llm/providers.py"
  - "src/processing/extractors.py"
  - "src/processing/ingest.py"
  - "src/processing/organizer.py"
  - "src/processing/pipeline.py"
  - "src/processing/split.py"
autonomous: true
requirements: []
---

# Plan 1: Refactor Source Structure

This plan reorganizes the flat `src/` directory into a modular structure (`core`, `llm`, `processing`) and updates all imports accordingly.

## 1. Move Core Modules

```xml
<task>
  <read_first>
    - src/schemas.py
    - src/config.py
    - src/cache.py
    - src/utils.py
  </read_first>
  <action>
    Create the `src/core` directory. Move `schemas.py`, `config.py`, `cache.py`, and `utils.py` from `src/` into `src/core/`. Create an empty `__init__.py` in `src/core/`.
  </action>
  <acceptance_criteria>
    - `src/core/schemas.py` exists
    - `src/core/config.py` exists
    - `src/core/cache.py` exists
    - `src/core/utils.py` exists
    - `src/schemas.py` no longer exists
  </acceptance_criteria>
</task>
```

## 2. Move LLM Modules

```xml
<task>
  <read_first>
    - src/llm.py
    - src/providers.py
  </read_first>
  <action>
    Create the `src/llm` directory. Move `llm.py` and `providers.py` from `src/` into `src/llm/`. Create an empty `__init__.py` in `src/llm/`.
  </action>
  <acceptance_criteria>
    - `src/llm/llm.py` exists
    - `src/llm/providers.py` exists
    - `src/llm.py` no longer exists
  </acceptance_criteria>
</task>
```

## 3. Move Processing Modules

```xml
<task>
  <read_first>
    - src/ingest.py
    - src/split.py
    - src/extractors.py
    - src/organizer.py
    - src/pipeline.py
  </read_first>
  <action>
    Create the `src/processing` directory. Move `ingest.py`, `split.py`, `extractors.py`, `organizer.py`, and `pipeline.py` from `src/` into `src/processing/`. Create an empty `__init__.py` in `src/processing/`.
  </action>
  <acceptance_criteria>
    - `src/processing/pipeline.py` exists
    - `src/processing/ingest.py` exists
    - `src/processing/split.py` exists
    - `src/processing/extractors.py` exists
    - `src/processing/organizer.py` exists
    - `src/pipeline.py` no longer exists
  </acceptance_criteria>
</task>
```

## 4. Fix Imports Across Codebase

```xml
<task>
  <read_first>
    - src/main.py
    - src/core/*.py
    - src/llm/*.py
    - src/processing/*.py
    - tests/*.py
    - scripts/*.py
  </read_first>
  <action>
    Update all internal python imports in all `.py` files inside `src/`, `tests/`, and `scripts/` to use the new module paths.
    For example, `import schemas` or `from schemas import ...` or `from src.schemas import ...` should become `from src.core.schemas import ...` (or relative `from ..core.schemas import ...` if preferred).
    Apply this to all imports pointing to `config`, `cache`, `schemas`, `utils`, `llm`, `providers`, `ingest`, `split`, `extractors`, `organizer`, and `pipeline`.
  </action>
  <acceptance_criteria>
    - `python -m py_compile src/main.py` completes without syntax errors.
    - `python src/main.py --help` executes without a `ModuleNotFoundError`.
    - The test suite runs successfully without import errors (e.g., `pytest tests/`).
  </acceptance_criteria>
</task>
```

## Verification

```yaml
must_haves:
  truths:
    - "src folder is partitioned into 'core', 'llm', and 'processing' subdirectories."
    - "No `ModuleNotFoundError` is thrown when invoking `src/main.py`."
    - "All internal imports across `src/`, `tests/`, and `scripts/` have been successfully migrated to the new package structure."
    - "The test suite executes successfully (e.g., `pytest tests/`) ensuring nothing was broken."
```

## Artifacts this phase produces

- **New Directories**:
  - `src/core/`
  - `src/llm/`
  - `src/processing/`
- **New Files**:
  - `src/core/__init__.py`
  - `src/llm/__init__.py`
  - `src/processing/__init__.py`
