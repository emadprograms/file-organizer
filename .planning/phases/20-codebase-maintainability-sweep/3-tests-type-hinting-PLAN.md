---
wave: 2
depends_on: []
files_modified:
  - tests/*.py
autonomous: true
requirements:
  - MAINT-01
---

# Plan 3: Tests Type Hinting

## Goal
Add complete Python type hints and Google-style docstrings to all fixtures, mocks, and test functions in the `tests/` directory.

<threat_model>
  <asvs_level>1</asvs_level>
  <block_on>high</block_on>
  <threats>
    - Type hinting should not introduce import loops or runtime dependencies that could cause denial of service.
    - Added docstrings must not expose sensitive internal logic or API secrets not already present in the code.
  </threats>
</threat_model>

<task>
  <action>Add complete Python 3.9+ type hints and Google-style docstrings to all fixtures, mocks, and test functions in `tests/test_core_*.py`, `tests/test_grouping_*.py`, and `tests/test_llm_*.py`. Also ensure `tests/conftest.py` is type-hinted and documented. Use built-in generics.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - tests/conftest.py
    - tests/test_core_config.py
    - tests/test_core_exceptions.py
    - tests/test_core_indexing.py
    - tests/test_core_schemas.py
    - tests/test_core_ui.py
    - tests/test_grouping_core.py
    - tests/test_grouping_core_contracts.py
    - tests/test_grouping_core_logic_config.py
    - tests/test_grouping_core_precision_window.py
    - tests/test_grouping_core_utility_bills.py
    - tests/test_llm_llm.py
    - tests/test_llm_llm_critical_error.py
    - tests/test_llm_llm_failure_isolation.py
    - tests/test_llm_llm_rate_limit.py
    - tests/test_llm_llm_resilience.py
    - tests/test_llm_llm_skip_mocking.py
    - tests/test_llm_providers.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" tests/test_core_*.py tests/test_grouping_*.py tests/test_llm_*.py` returns no results
    - `grep -r "typing.Dict" tests/test_core_*.py tests/test_grouping_*.py tests/test_llm_*.py` returns no results
    - Test functions have Google-style docstrings explaining the scenario and expected outcome
    - Fixtures and mocks have appropriate return types (e.g. `-> None` for tests)
  </acceptance_criteria>
</task>

<task>
  <action>Add complete Python 3.9+ type hints and Google-style docstrings to all fixtures, mocks, and test functions in `tests/test_main_*.py`, `tests/test_pdf_*.py`, `tests/test_pipeline_*.py`, `tests/test_tenant_config_*.py`, `tests/test_timeline_*.py`, and `tests/test_utils_*.py`. Use built-in generics.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - tests/test_main_cli.py
    - tests/test_main_file_placement.py
    - tests/test_main_logging_e2e.py
    - tests/test_pdf_extract_compress.py
    - tests/test_pdf_extract_split.py
    - tests/test_pipeline_core.py
    - tests/test_pipeline_core_routing.py
    - tests/test_pipeline_e2e.py
    - tests/test_pipeline_e2e_continuity.py
    - tests/test_pipeline_e2e_default.py
    - tests/test_pipeline_e2e_others.py
    - tests/test_pipeline_visualizer.py
    - tests/test_pipeline_yaml_pipeline.py
    - tests/test_tenant_config_yaml_loader.py
    - tests/test_timeline_cleaning.py
    - tests/test_timeline_core_edge_cases.py
    - tests/test_timeline_reconciliation.py
    - tests/test_utils_fs.py
    - tests/test_utils_logger.py
    - tests/test_utils_logger_audit.py
    - tests/test_utils_logger_dual.py
    - tests/test_utils_logger_exceptions.py
    - tests/test_utils_logger_jsonl_trace.py
    - tests/test_utils_logger_trace_refactor.py
    - tests/test_utils_telemetry_audit.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" tests/test_main_*.py tests/test_pdf_*.py tests/test_pipeline_*.py tests/test_tenant_config_*.py tests/test_timeline_*.py tests/test_utils_*.py` returns no results
    - Test functions have Google-style docstrings explaining the scenario and expected outcome
  </acceptance_criteria>
</task>

<task>
  <action>Add complete Python 3.9+ type hints and Google-style docstrings to all fixtures, mocks, and test functions in `tests/test_routing_*.py`. Use built-in generics.</action>
  <read_first>
    - .planning/phases/20-codebase-maintainability-sweep/20-PATTERNS.md
    - tests/test_routing_router.py
    - tests/test_routing_router_arabic_names.py
    - tests/test_routing_router_constrained_forms.py
    - tests/test_routing_router_constrained_letters.py
    - tests/test_routing_router_direct_scenarios.py
    - tests/test_routing_router_escape_hatch.py
    - tests/test_routing_router_finalization.py
    - tests/test_routing_router_hallucination.py
    - tests/test_routing_router_logic.py
    - tests/test_routing_router_normal.py
    - tests/test_routing_router_others_flow.py
    - tests/test_routing_router_safety.py
    - tests/test_routing_router_schema.py
    - tests/test_routing_state_logic.py
  </read_first>
  <acceptance_criteria>
    - `grep -r "typing.List" tests/test_routing_*.py` returns no results
    - Test functions have Google-style docstrings explaining the scenario and expected outcome
  </acceptance_criteria>
</task>

## Verification
- Run `pytest` to ensure test behavior and runtime behavior is correct and tests pass.

## must_haves

```yaml
must_haves:
  truths:
    - "D-04: tests/ directory type-hinted and documented to maximize maintainability."
    - "D-03: Docstrings present for every single test function, fixture, and mock."
    - "D-01: Hints added for IDE autocomplete only, no strict type checker setup."
    - "D-02: Modern Python 3.9+ built-in generics used for all type hints in tests."
  prohibitions: []
```

## Artifacts this phase produces
- No new symbols (decorators, classes, functions, CLI flags, struct/dataclass fields, new file paths) are created in this plan. Only docstrings and type hints are added to existing codebase files.
