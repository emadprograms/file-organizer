---
wave: 1
depends_on: []
files_modified:
  - src/grouping/name_matcher.py
  - src/timeline/timeline_builder.py
  - src/tenant_config/tenants.py
  - src/timeline/phase.py
autonomous: true
---

# Phase 19.1.1 Plan: Refactor tenant matching logic

## Goal
Refactor tenant matching logic out of `tenant_config/tenants.py` into appropriate module boundaries according to Phase 16 architecture.

## Artifacts this phase produces
- New file: `src/grouping/name_matcher.py`
- New file: `src/timeline/timeline_builder.py`

## must_haves

```yaml
must_haves:
  truths:
    - src/grouping/name_matcher.py exists and contains normalize_arabic_text, cluster_names_fuzzily, and canonicalize_with_llm
    - src/timeline/timeline_builder.py exists and contains build_tenant_timelines
    - src/tenant_config/tenants.py no longer contains the migrated functions
    - src/timeline/phase.py imports the functions from their new module locations
  prohibitions: []
```

## Tasks

### Wave 1: Migration

<task>
<action>
Create `src/grouping/name_matcher.py` and migrate `normalize_arabic_text`, `cluster_names_fuzzily`, and `canonicalize_with_llm` from `src/tenant_config/tenants.py`. Update the LLM prompt inside `canonicalize_with_llm` to accept the tenant names from the YAML and ask: "Is this name similar to any of the names here?"
</action>
<read_first>
- src/tenant_config/tenants.py
- .planning/phases/19.1.1-close-gap-pipe-02-refactor-tenant-matching-logic-from-tenant/19.1.1-PATTERNS.md
</read_first>
<acceptance_criteria>
- `src/grouping/name_matcher.py` exists and contains the functions `normalize_arabic_text`, `cluster_names_fuzzily`, and `canonicalize_with_llm`.
- The original logic and signatures of `normalize_arabic_text` and `cluster_names_fuzzily` remain unchanged.
- `canonicalize_with_llm` is updated to accept the tenant names from the YAML and its prompt includes: "Is this name similar to any of the names here?".
</acceptance_criteria>
</task>

<task>
<action>
Create `src/timeline/timeline_builder.py` and migrate `build_tenant_timelines` from `src/tenant_config/tenants.py`.
</action>
<read_first>
- src/tenant_config/tenants.py
- .planning/phases/19.1.1-close-gap-pipe-02-refactor-tenant-matching-logic-from-tenant/19.1.1-PATTERNS.md
</read_first>
<acceptance_criteria>
- `src/timeline/timeline_builder.py` exists and contains the function `build_tenant_timelines`.
- The original logic and signature of the function remains unchanged.
</acceptance_criteria>
</task>

### Wave 2: Cleanup and Import Updates

<task>
<action>
Remove the migrated functions (`normalize_arabic_text`, `cluster_names_fuzzily`, `canonicalize_with_llm`, `build_tenant_timelines`) from `src/tenant_config/tenants.py` and update imports in `src/timeline/phase.py` (and any other files that imported them) to point to `src/grouping/name_matcher.py` and `src/timeline/timeline_builder.py`.
</action>
<read_first>
- src/tenant_config/tenants.py
- src/timeline/phase.py
</read_first>
<acceptance_criteria>
- `src/tenant_config/tenants.py` no longer contains the definitions for `normalize_arabic_text`, `cluster_names_fuzzily`, `canonicalize_with_llm`, or `build_tenant_timelines`.
- `src/timeline/phase.py` has updated imports pointing to `src.grouping.name_matcher` and `src.timeline.timeline_builder`.
- `python -m py_compile src/timeline/phase.py` exits with 0 (no syntax errors).
</acceptance_criteria>
</task>

## Verification
- Code successfully executes the phase logic.
- Verify that `src/tenant_config/tenants.py` no longer contains the aforementioned functions.
- Verify that no old imports to those functions remain across the codebase.
