---
wave: 1
depends_on: []
files_modified:
  - src/core/*.py
  - src/utils/*.py
  - src/llm/*.py
  - src/pipeline/*.py
  - src/main.py
  - rotate_process.py
autonomous: true
requirements:
  - MAINT-01
---

# Plan 1: Domain and Orchestration Type Hinting

## Goal
Add complete Python type hints and Google-style docstrings to domain modules and the main orchestrator script in `src/`.

<threat_model>
  <asvs_level>1</asvs_level>
  <block_on>high</block_on>
  <threats>
    - Type hinting should not introduce import loops or runtime dependencies that could cause denial of service.
    - Added docstrings must not expose sensitive internal logic or API secrets not already present in the code.
  </threats>
</threat_model>

<task>
  <action>Add complete Python 3.9+ type hints (`list[str]`, `dict[str, Any]`, etc. instead of `typing.List`/`typing.Dict`) and Google-style docstrings to all functions and classes in `src/core/*.py` (`config.py`, `exceptions.py`, `indexing.py`, `models.py`, `schemas.py`, `ui.py`, `utils.py`). Include private methods. Remove any legacy `typing.List` or `typing.Dict` imports and usages.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - src/core/config.py
    - src/core/exceptions.py
    - src/core/indexing.py
    - src/core/models.py
    - src/core/schemas.py
    - src/core/ui.py
    - src/core/utils.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" src/core/` returns no results
    - `grep -r "typing.Dict" src/core/` returns no results
    - All functions and classes in `src/core/*.py` have Google-style docstrings containing `Args:`, `Returns:`, and `Raises:` where applicable
    - Type hints use built-in generics like `list[str]` or `dict[str, Any]`
  </acceptance_criteria>
</task>

<task>
  <action>Add complete Python 3.9+ type hints and Google-style docstrings to all functions and classes in `src/utils/*.py` (`fs.py`, `logger.py`). Include private methods and replace legacy typing imports with built-in generics.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - src/utils/fs.py
    - src/utils/logger.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" src/utils/` returns no results
    - All functions and classes in `src/utils/*.py` have Google-style docstrings
    - Type hints use built-in generics like `list[str]` or `dict[str, Any]`
  </acceptance_criteria>
</task>

<task>
  <action>Add complete Python 3.9+ type hints and Google-style docstrings to all functions and classes in `src/llm/*.py` (`llm.py`, `mock.py`, `providers.py`). Include private methods like `_route_llm_call` as shown in PATTERNS.md.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - src/llm/llm.py
    - src/llm/mock.py
    - src/llm/providers.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" src/llm/` returns no results
    - `src/llm/llm.py` contains a complete docstring for `_route_llm_call` matching the pattern in PATTERNS.md
    - All functions and classes in `src/llm/*.py` have Google-style docstrings
    - Type hints use built-in generics
  </acceptance_criteria>
</task>

<task>
  <action>Add complete Python 3.9+ type hints and Google-style docstrings to `src/main.py`, `rotate_process.py` and `src/pipeline/*.py` (`pipeline.py`, `visualizer.py`). Document all CLI endpoints and orchestrator functions. Use built-in generics.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - src/main.py
    - rotate_process.py
    - src/pipeline/pipeline.py
    - src/pipeline/visualizer.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" src/pipeline/` returns no results
    - `grep "typing.List" src/main.py rotate_process.py` returns no results
    - `src/main.py`, `rotate_process.py` and `src/pipeline/*.py` functions and classes have Google-style docstrings
    - Complex return types (e.g. `dict[str, int]`) are correctly hinted using built-ins
  </acceptance_criteria>
</task>

## Verification
- Run `pytest` to ensure type hinting did not break runtime behavior.

## must_haves

```yaml
must_haves:
  truths:
    - "D-03: Docstrings present for every single function and class, including private methods in `src/core`, `src/utils`, `src/llm`, `src/pipeline`, `src/main.py` and `rotate_process.py`."
    - "D-01: Hints added for IDE autocomplete only, no strict type checker setup."
    - "D-02: Modern Python 3.9+ built-in generics used for all type hints."
  prohibitions: []
```

## Artifacts this phase produces
- No new symbols (decorators, classes, functions, CLI flags, struct/dataclass fields, new file paths) are created in this plan. Only docstrings and type hints are added to existing codebase files.
