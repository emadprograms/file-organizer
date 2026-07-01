---
version: 1.0
phase: 1
autonomous: true
wave: 1
requirements: [CONF-01, CONF-02, CONF-03]
depends_on: []
files_modified:
  - requirements.txt
  - src/schemas.py
  - src/config.py
  - src/main.py
  - sample-config.yaml
  - test-config.yaml
  - .gitignore
---

# Phase 1: Configuration Infrastructure - Plan

<threat_model>
<asvs_level>1</asvs_level>
<block_on>high</block_on>
<threats>
  - Malicious YAML payload (e.g., arbitrary code execution via unsafe load). Mitigation: `yaml.safe_load` will be explicitly used instead of `yaml.load` when parsing configuration files.
</threats>
</threat_model>

## Goal
Build the core capability to parse and validate user-provided YAML/JSON configuration files, establishing the foundation for a config-driven pipeline.

## Artifacts this phase produces
- **File**: `sample-config.yaml`
- **File**: `test-config.yaml`
- **Dependency**: `PyYAML` added to `requirements.txt`
- **Class**: `UserConfig` in `src/schemas.py`
- **Class**: `ConfigCategory` in `src/schemas.py`
- **Class**: `ConfigExtraction` in `src/schemas.py`
- **Class**: `ConfigRouting` in `src/schemas.py`
- **Function**: `load_user_config` in `src/config.py`
- **Class**: `InvalidConfigError` in `src/config.py`
- **CLI Flag**: `-c` / `--config` added to `src/main.py`

## must_haves
- truths:
  - D-01: The CLI accepts a `--config` flag to override the default config path.
  - D-01: The system loads `./config.yaml` by default if `--config` is not provided.
  - D-04: `sample-config.yaml` exists in the repository root and contains valid YAML reflecting the 13 categories.
  - D-03: The system fails fast with `InvalidConfigError` and a clear error message when an invalid configuration is provided.
  - D-02: Pydantic models rigorously validate the parsed configuration file structure.
  - Configuration parsing uses `yaml.safe_load` to mitigate arbitrary code execution.

## Tasks

<task>
<id>1</id>
<title>Add PyYAML Dependency</title>
<read_first>
  - requirements.txt
</read_first>
<action>
Add `PyYAML` to `requirements.txt` to support parsing YAML configuration files.
</action>
<acceptance_criteria>
  - `requirements.txt` contains `PyYAML` on its own line
</acceptance_criteria>
</task>

<task>
<id>2</id>
<title>Define User Configuration Schemas</title>
<read_first>
  - src/schemas.py
  - .planning/phases/01-configuration-infrastructure/01-CONTEXT.md
</read_first>
<action>
In `src/schemas.py`, add Pydantic models for the user configuration:
- `ConfigCategory`: A model for a document category (fields: `id`, `name`).
- `ConfigExtraction`: A model for extraction instructions (fields: `prompt_rules`).
- `ConfigRouting`: A model for organization rules (fields: `destination_format`).
- `UserConfig`: The root model encompassing `categories` (list of `ConfigCategory`), `extraction` (`ConfigExtraction`), and `routing` (`ConfigRouting`).
</action>
<acceptance_criteria>
  - `src/schemas.py` contains `class UserConfig(BaseModel):`
  - `UserConfig` includes fields for categories, extraction, and routing.
</acceptance_criteria>
</task>

<task>
<id>3</id>
<title>Implement User Config Loader</title>
<read_first>
  - src/config.py
  - src/schemas.py
</read_first>
<action>
In `src/config.py`, create a `load_user_config(config_path: Path) -> UserConfig` function.
It should read the file (`.yaml` or `.json`), parse it securely with `yaml.safe_load` or `json.load`, and validate it by instantiating `UserConfig`.
Create an `InvalidConfigError(Exception)` class in `src/config.py`, and raise it with a clear, fast-fail error message if validation or file reading fails.
</action>
<acceptance_criteria>
  - `src/config.py` contains `def load_user_config` returning `UserConfig`
  - `src/config.py` uses `yaml.safe_load` (not `yaml.load`)
  - `src/config.py` contains `class InvalidConfigError(Exception):`
</acceptance_criteria>
</task>

<task>
<id>4</id>
<title>Update CLI Configuration Discovery</title>
<read_first>
  - src/main.py
  - src/config.py
</read_first>
<action>
In `src/main.py`, update the `argparse.ArgumentParser` setup to add a `-c` / `--config` flag, defaulting to `"config.yaml"`.
Before running the pipeline, call `load_user_config` with the resolved path. If it raises `InvalidConfigError` or `FileNotFoundError` (when explicitly specified), catch it, call `logger.error` with the exception message, and call `sys.exit(1)`.
Store the returned `UserConfig` object in a local variable `user_config` in `main()` so it can be passed to downstream components in later phases.
</action>
<acceptance_criteria>
  - `src/main.py` contains `parser.add_argument("-c", "--config"`
  - `src/main.py` catches `InvalidConfigError` and calls `sys.exit(1)`
</acceptance_criteria>
</task>

<task>
<id>5</id>
<title>Create Sample Configuration</title>
<read_first>
  - src/schemas.py
</read_first>
<action>
Create a `sample-config.yaml` file at the root of the project.
This file should contain a `categories` list mapping to the 13 categories (e.g., `BASIC_DETAILS`, `PERSONAL_DETAILS`) defined in the `Category` enum inside `src/schemas.py`.
Include placeholders for `extraction` and `routing` sections that reflect the schema defined in `UserConfig`.
</action>
<acceptance_criteria>
  - `sample-config.yaml` exists at the root.
  - The file contains valid YAML syntax and includes the `BASIC_DETAILS` category.
</acceptance_criteria>
</task>

<task>
<id>6</id>
<title>Create Private Local Config & Update gitignore</title>
<read_first>
  - .gitignore
</read_first>
<action>
Add `config.yaml` and `test-config.yaml` to `.gitignore`.
Create a `test-config.yaml` at the root that mirrors `sample-config.yaml` for use in local regression testing.
</action>
<acceptance_criteria>
  - `.gitignore` ignores `config.yaml` and `test-config.yaml`
  - `test-config.yaml` exists at the root.
</acceptance_criteria>
</task>

## Verification
- Ensure `python -c "from src.config import load_user_config; from pathlib import Path; load_user_config(Path('sample-config.yaml'))"` executes successfully.
- Ensure running `python src/main.py non_existent.pdf --config invalid-config.yaml` exits with a clear error message logged.
