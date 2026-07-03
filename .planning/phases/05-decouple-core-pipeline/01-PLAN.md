---
wave: 1
depends_on: []
files_modified:
  - "src/schemas.py"
  - "src/llm.py"
  - "src/pipeline.py"
  - "src/organizer.py"
autonomous: true
---

# Phase 05: Decouple Core Pipeline

## Goal
Remove all hardcoded domain logic from the core pipeline engine and verify via the scripts from Phase 4.

## Requirements
- REF-01: Refactor `src/llm.py` to extract domain-specific prompts.
- REF-02: Refactor `src/organizer.py` to remove hardcoded folder structures and entity parsing.
- REF-03: Refactor `src/pipeline.py` to eliminate hardcoded heuristic strategies.

## Tasks

### Wave 1: Schema, Config Validation, and LLM Decoupling

<task>
<read_first>
- src/schemas.py
- src/llm.py
- src/pipeline.py
</read_first>
<action>
1. Define Pydantic schemas for the configuration file (e.g., in `src/schemas.py` or a dedicated config module) to validate the config automatically at pipeline startup (D-04).
2. Remove `Category` Enum completely from `src/schemas.py`. Allowed string category values should instead be defined in the config and mapped dynamically (D-11).
3. Remove `PageClassification` BaseModel from `src/schemas.py`. It must be built dynamically inside `src/llm.py` using extraction schema fields (name, type, description) defined in the config (D-10).
4. Change `DocumentGroup.category` type in `src/schemas.py` from `Category` to `str`.
5. Remove `_build_system_prompt()` method from `LLMClient` in `src/llm.py`, expecting domain-specific prompts via config using simple string formatting (e.g. `{text}`) (D-09).
6. Update `LLMClient.cluster_names`, `LLMClient.detect_date_outliers`, and `LLMClient.check_bulk_semantic_grouping` in `src/llm.py` to accept a `prompt_template: str` parameter and use it instead of hardcoded strings, ensuring all secondary prompts are fully configurable (D-12).
</action>
<acceptance_criteria>
- Configuration is validated via Pydantic at startup.
- `grep "Category(str, Enum):" src/schemas.py` returns no results.
- `grep "class PageClassification(BaseModel):" src/schemas.py` returns no results.
- `grep "def _build_system_prompt" src/llm.py` returns no results.
- `src/llm.py` executes LLM queries using the dynamically injected `prompt_template` string variables.
</acceptance_criteria>
</task>

### Wave 2: Pipeline Orchestration and Fallback

<task>
<read_first>
- src/pipeline.py
</read_first>
<action>
1. Update cache loading in `src/pipeline.py`: remove the strict `result = PageClassification(**cache_data)` validation, instead load the raw dict or construct the dynamic schema class (via `create_model`) to parse it.
2. In `src/pipeline.py`, when calling `self.client.detect_date_outliers`, `self.client.cluster_names`, and `self.client.check_bulk_semantic_grouping`, pass the corresponding prompt string from `config.cleaning.prompts` (e.g. `config.cleaning.prompts.get('date_outliers', '')`).
3. Replace the hardcoded Python grouping strategy in Pass 2 with dynamic loading of the script specified by `config.grouping.script_path`. Ensure this script resides in a dedicated `scripts/` folder outside `src/` (D-05). Use `importlib.util` to load the module and invoke its `group_pages(raw_pages, client)` function directly using a functional approach (D-06).
4. Catch exceptions if the grouping script fails (or if no script is specified), log the errors (D-07), and fallback to a built-in strict default grouping strategy that enforces grouping constraints specified in the config (e.g., max page limit and allowed category sets) (D-03, D-08).
</action>
<acceptance_criteria>
- `grep "PageClassification(" src/pipeline.py` returns no hardcoded class instantiations.
- `importlib.util.spec_from_file_location` is used to load the Python module from `config.grouping.script_path`.
- The pipeline executes without crashing when `config.grouping.script_path` is invalid by falling back to sequential grouping.
</acceptance_criteria>
</task>

### Wave 3: Organizer Externalization

<task>
<read_first>
- src/organizer.py
</read_first>
<action>
1. Remove `CATEGORY_FOLDERS` map, `_resolve_house_number()`, `_compute_tenant_timelines()`, and `_build_resident_order()` from `FileOrganizer` in `src/organizer.py`.
2. Rewrite `FileOrganizer.organize()` to check if `config.routing.strategy == "python"` and `config.routing.script_path` is set.
3. If true, load the script via `importlib.util` and invoke its `organize(documents, source_pdf, output_base_dir)` function directly (functional approach) (D-06). Ensure routing scripts are also stored in the `scripts/` directory (D-05).
4. If false or the script fails, catch and log any errors (D-07), then fallback to a declarative strategy that iterates `documents`, looks up the destination folder using a simple key-value mapping from `config.routing.rules` (where keys are categories, values are destination folders) (D-01), and falls back to `config.routing.fallback_folder` for unmapped categories (D-02). Extracts the PDF segments to the target paths.
</action>
<acceptance_criteria>
- `grep "CATEGORY_FOLDERS =" src/organizer.py` returns no results.
- `grep "def _compute_tenant_timelines" src/organizer.py` returns no results.
- `importlib.util` successfully loads the python script defined in `config.routing.script_path`.
</acceptance_criteria>
</task>

## Artifacts this phase produces
- Refactored existing `src/` modules. Legacy fallback scripts will be located in the `scripts/` directory (D-05).

## Verification Criteria
- `pytest` tests pass.
- Running the pipeline with `sample-config.yaml` produces exactly the same output as the hardcoded version in Phase 4.

## Must Haves

<must_haves>
  <truths>
    - `src/llm.py` contains no Bahrain housing specific prompts and relies on config-defined templates using simple formatting (D-09, D-12).
    - `src/organizer.py` relies strictly on YAML-defined rules or dynamically loaded python scripts.
    - `src/pipeline.py` no longer contains real-estate specific heuristics.
    - A test execution of the pipeline completes successfully, proving backward compatibility.
    - Fallback logic scripts are stored in a dedicated `scripts/` folder and invoked directly as functions (D-05, D-06).
  </truths>
  <prohibitions>
    - `src/schemas.py` MUST NOT contain the `Category` enum.
    - `src/organizer.py` MUST NOT contain the `CATEGORY_FOLDERS` constant.
  </prohibitions>
</must_haves>

<threat_model>
ASVS Level: 1
Blocking Threshold: high

### Threat 1: Malicious Script Execution
- **Description:** The system uses `importlib.util` to load arbitrary Python scripts from paths specified in the YAML configuration (`config.grouping.script_path`, `config.routing.script_path`). If a user can inject a malicious YAML config, they gain arbitrary code execution.
- **Mitigation:** The application is explicitly a local CLI tool designed to run local configurations provided by the executing user. There is no remote user input vector for the configuration file, so the threat is accepted as part of the intended local operational model.

### Threat 2: Path Traversal via Config
- **Description:** The `fallback_folder` or `destination_format` in `config.routing` might contain path traversal characters (`../`), allowing files to be written outside the intended output directory.
- **Mitigation:** The core pipeline should sanitize or `Path.resolve()` output paths and verify they reside within the `output_base_dir`.
</threat_model>
