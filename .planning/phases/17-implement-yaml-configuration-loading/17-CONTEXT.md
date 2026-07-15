# Phase 17: Implement YAML Configuration Loading (tenant_config) - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Create logic to find the root folder "source files" and extract primary tenant names from a `tenants.yaml` configuration file, preparing them for pipeline consumption.

</domain>

<decisions>
## Implementation Decisions

### YAML Structure
- **D-01:** The `tenants.yaml` file will contain a simple list of strings (no complex dictionary required). The current codebase logic handles timeline bounds, so extra fields are not needed.

### Path Resolution
- **D-02:** The configuration will be loaded from a file specifically named `tenants.yaml` located in the "source files" directory.

### Validation Strategy
- **D-03:** Pydantic schema model validation will be used to strictly validate the loaded YAML data, matching the project's existing validation patterns in `src/core/models.py`.

### Translation Strategy
- **D-04:** The tenant names in the YAML file will be written in English. The application logic is responsible for translating these names to Arabic.

### Claude's Discretion
None

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & Requirements
- `.planning/PROJECT.md` — Defines the Logic-Based Modular Refactoring constraints
- `.planning/REQUIREMENTS.md` § Epic: YAML Integration — Epic YAML constraints

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/core/models.py`: Use this to define the Pydantic schema model for `tenants.yaml` validation.
- `src/tenant_config/tenants.py`: Contains the existing old anchor logic that will be eventually replaced/modified (per PIPE-01 and PIPE-02, although this phase only handles loading the yaml).

### Established Patterns
- Pydantic models for structured data validation.
- Unified hierarchical `LogContext` structured JSON logging.

### Integration Points
- YAML parsing will sit in a new `src/tenant_config/yaml_reader.py` module.
- Validation should tie into `src/core/models.py`.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 17-Implement YAML Configuration Loading*
*Context gathered: 2026-07-15*
