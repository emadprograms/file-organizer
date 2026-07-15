# Phase 17 Research

## Context
Phase 17 transitions the pipeline from relying on LLMs for canonicalizing tenant names to a deterministic, user-provided YAML configuration file. 

## Requirements
- **Location**: The YAML configuration file (e.g., `tenants.yaml`) will be placed in the same directory as the input PDF and `report.json` (i.e. the `target_dir` passed to the pipeline).
- **Structure**: A simple list of primary tenant names under a `tenants` key.
  Example:
  ```yaml
  tenants:
    - "Tenant Name A"
    - "Tenant Name B"
  ```
- **Dependencies**: `PyYAML` is already present in `requirements.txt`.
- **Implementation**: Needs logic to locate `tenants.yaml` inside `target_dir`, parse it, and return the list of primary tenant names. This functionality belongs in the `src/tenant_config` module.
