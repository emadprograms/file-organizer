---
version: 1.0
wave: 1
depends_on: []
files_modified:
  - sample-config.yaml
  - src/schemas.py
  - scripts/sample-routing.py
  - scripts/sample-grouping.py
autonomous: true
requirements:
  - REF-04
---

# Phase 4 Plan: Legacy Logic Porting & Verification

<threat_model>
- ASVS Level: 1
- Block on: high
- Threat: Malicious prompts or external scripts introduced into configuration files leading to prompt injection or arbitrary code execution.
- Mitigation: This phase only ports existing hardcoded logic into fallback scripts and sample configs. These configs are considered trusted files, but they will eventually be loaded by the pipeline. No untrusted user data is being evaluated during this porting phase.
</threat_model>

## must_haves

```yaml
must_haves:
  truths:
    - sample-config.yaml contains prompts for entity_resolution, date_outliers, and semantic_grouping under the cleaning block.
    - ConfigCleaning in src/schemas.py supports the new prompts dictionary.
    - sample-routing.py replicates the CATEGORY_FOLDERS and logic from src/organizer.py.
    - sample-grouping.py replicates the grouping logic from src/pipeline.py.
  prohibitions: []
```

## Tasks

```xml
<task>
  <action>
    CRITICAL (PREVIOUSLY SKIPPED - MUST COMPLETE): Extract the hardcoded LLM prompts from `src/llm.py` (specifically the `system_prompt` from `cluster_names`, `check_date_outliers`, and `check_bulk_semantic_grouping`) and add them as a new `prompts` dictionary within the `cleaning:` block of `sample-config.yaml`. The keys should be `entity_resolution`, `date_outliers`, and `semantic_grouping`. Also, update `src/schemas.py` to add `prompts: dict[str, str] | None = Field(default=None, description="Dictionary of specific LLM prompts for cleaning steps")` to the `ConfigCleaning` class to pass Pydantic validation. DO NOT SKIP THIS.
  </action>
  <read_first>
    - src/llm.py
    - sample-config.yaml
    - src/schemas.py
  </read_first>
  <acceptance_criteria>
    - `src/schemas.py` ConfigCleaning class has a `prompts` field of type `dict[str, str] | None`.
    - `sample-config.yaml` contains `prompts:` under the `cleaning:` block.
    - `sample-config.yaml` contains the exact text "You are an expert at entity resolution for Bahrain housing documents." under `cleaning.prompts.entity_resolution`.
    - `sample-config.yaml` contains the exact text "Analyze the following sequence of document dates" under `cleaning.prompts.date_outliers`.
    - `sample-config.yaml` contains the exact text "You are a logical document grouping assistant" under `cleaning.prompts.semantic_grouping`.
  </acceptance_criteria>
</task>

<task>
  <action>
    COMPLETED: Review `scripts/sample-routing.py` and `scripts/sample-grouping.py` against `src/organizer.py` and `src/pipeline.py` to ensure all Bahrain-specific domain logic, category Arabic translations (e.g., "01_البيانات الاساسية"), and tenant timeline suffixes (e.g., " - الساكن الحالي") are perfectly replicated. Update the scripts if any differences exist so they are a 1:1 port of the legacy behavior. Ensure they don't drift from the actual implementation before we delete it in phase 5.
  </action>
  <read_first>
    - src/organizer.py
    - src/pipeline.py
    - scripts/sample-routing.py
    - scripts/sample-grouping.py
  </read_first>
  <acceptance_criteria>
    - `scripts/sample-routing.py` contains `CATEGORY_FOLDERS` matching exactly the keys and Arabic string values in `src/organizer.py`.
    - `scripts/sample-routing.py` contains the exact timeline suffix logic (`" - الساكن الحالي"`).
    - `scripts/sample-grouping.py` contains the matching chunk_size and fallback logic for `all_groups.extend(block_groups)` found in `src/pipeline.py`.
  </acceptance_criteria>
</task>
```

## Artifacts this phase produces

- Configuration keys added to `sample-config.yaml`: `cleaning.prompts.entity_resolution`, `cleaning.prompts.date_outliers`, `cleaning.prompts.semantic_grouping`.
- New struct field in `src/schemas.py`: `ConfigCleaning.prompts`.
- Verified and optionally updated external Python scripts: `scripts/sample-routing.py`, `scripts/sample-grouping.py`.
