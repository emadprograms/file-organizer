---
wave: 1
depends_on: []
files_modified:
  - src/grouping/*.py
  - src/routing/*.py
  - src/timeline/*.py
  - src/pdf/*.py
  - src/tenant_config/*.py
autonomous: true
requirements:
  - MAINT-01
---

# Plan 2: Pipeline Logic Type Hinting

## Goal
Add complete Python type hints and Google-style docstrings to pipeline functional modules in `src/`.

<threat_model>
  <asvs_level>1</asvs_level>
  <block_on>high</block_on>
  <threats>
    - Type hinting should not introduce import loops or runtime dependencies that could cause denial of service.
    - Added docstrings must not expose sensitive internal logic or API secrets not already present in the code.
  </threats>
</threat_model>

<task>
  <action>Add complete Python 3.9+ type hints and Google-style docstrings to all functions and classes in `src/grouping/*.py` (`config.py`, `core.py`, `name_matcher.py`, `state.py`, `utils.py`). Include private methods and replace `typing.List`/`typing.Dict` with built-in generics.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - src/grouping/config.py
    - src/grouping/core.py
    - src/grouping/name_matcher.py
    - src/grouping/state.py
    - src/grouping/utils.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" src/grouping/` returns no results
    - `grep -r "typing.Dict" src/grouping/` returns no results
    - All functions and classes in `src/grouping/*.py` have Google-style docstrings
    - Functions modifying state use generic types like `list[DocumentGroup]`
  </acceptance_criteria>
</task>

<task>
  <action>Add complete Python 3.9+ type hints and Google-style docstrings to all functions and classes in `src/routing/*.py` (`config.py`, `router.py`, `state.py`). Include private methods and replace legacy typing imports with built-in generics.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - src/routing/config.py
    - src/routing/router.py
    - src/routing/state.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" src/routing/` returns no results
    - All functions and classes in `src/routing/*.py` have Google-style docstrings
  </acceptance_criteria>
</task>

<task>
  <action>Add complete Python 3.9+ type hints and Google-style docstrings to all functions and classes in `src/timeline/*.py` (`core.py`, `dates.py`, `phase.py`, `reconciliation.py`, `timeline_builder.py`). Include private methods and use built-in generics.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - src/timeline/core.py
    - src/timeline/dates.py
    - src/timeline/phase.py
    - src/timeline/reconciliation.py
    - src/timeline/timeline_builder.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" src/timeline/` returns no results
    - All functions and classes in `src/timeline/*.py` have Google-style docstrings
  </acceptance_criteria>
</task>

<task>
  <action>Add complete Python 3.9+ type hints and Google-style docstrings to all functions and classes in `src/pdf/*.py` (`compress.py`, `extract.py`) and `src/tenant_config/*.py` (`tenants.py`, `yaml_loader.py`). Include private methods and use built-in generics.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - src/pdf/compress.py
    - src/pdf/extract.py
    - src/tenant_config/tenants.py
    - src/tenant_config/yaml_loader.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" src/pdf/` returns no results
    - `grep -r "typing.List" src/tenant_config/` returns no results
    - All functions and classes in `src/pdf/*.py` and `src/tenant_config/*.py` have Google-style docstrings
  </acceptance_criteria>
</task>

## Verification
- Run `pytest` to ensure type hinting did not break runtime behavior.

## must_haves

```yaml
must_haves:
  truths:
    - "D-03: Docstrings present for every single function and class, including private methods in pipeline modules."
    - "D-01: Hints added for IDE autocomplete only, no strict type checker setup."
    - "D-02: Modern Python 3.9+ built-in generics used for all type hints."
  prohibitions: []
```

## Artifacts this phase produces
- No new symbols (decorators, classes, functions, CLI flags, struct/dataclass fields, new file paths) are created in this plan. Only docstrings and type hints are added to existing codebase files.
