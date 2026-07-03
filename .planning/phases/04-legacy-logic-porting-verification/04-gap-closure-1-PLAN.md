---
version: 1.0
wave: 1
depends_on: []
files_modified:
  - sample-config.yaml
  - tests/test_fallback_chain.py
autonomous: true
requirements:
  - REF-04
---

# Phase 4 Gap Closure 1 Plan

<threat_model>
- ASVS Level: 1
- Block on: high
- Threat: Improper test fixes could mask integration issues.
- Mitigation: Fixes apply strictly to the test suite and correct prompt text matching. No runtime execution behavior is modified.
</threat_model>

## must_haves

```yaml
must_haves:
  truths:
    - `sample-config.yaml` contains the exact text "You are a logical document grouping assistant" under `cleaning.prompts.semantic_grouping`.
    - Test suite passes without `TypeError: LLMClient.cluster_names() missing 1 required positional argument: 'other_names'`.
  prohibitions: []
```

## Tasks

```xml
<task>
  <action>
    Fix the prompt text mismatch in `sample-config.yaml`. Change the `semantic_grouping` prompt under the `cleaning:` block to exactly match "You are a logical document grouping assistant" instead of the current text "You are an expert document organizer analyzing a sequence of pages from a single property file."
  </action>
  <read_first>
    - sample-config.yaml
  </read_first>
  <acceptance_criteria>
    - `sample-config.yaml` contains the exact text "You are a logical document grouping assistant" under `cleaning.prompts.semantic_grouping`.
  </acceptance_criteria>
</task>

<task>
  <action>
    Fix the broken test `test_mocked_fallback_chain_integration` in `tests/test_fallback_chain.py`. It fails with `TypeError: LLMClient.cluster_names() missing 1 required positional argument: 'other_names'`. Ensure the mocked call correctly supplies or handles the `other_names` argument.
  </action>
  <read_first>
    - tests/test_fallback_chain.py
  </read_first>
  <acceptance_criteria>
    - Running `pytest tests/test_fallback_chain.py` passes successfully.
  </acceptance_criteria>
</task>
```

## Artifacts this phase produces

- Updated `sample-config.yaml`.
- Fixed `tests/test_fallback_chain.py`.
