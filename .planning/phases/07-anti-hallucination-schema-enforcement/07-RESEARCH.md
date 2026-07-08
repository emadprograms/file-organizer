# Phase 07: Anti-Hallucination Schema Enforcement - Research

**Researched:** 2024-05-22
**Domain:** LLM Structured Output & Schema Validation
**Confidence:** HIGH

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Dynamic Schema Enforcement (Critical)**: Instead of relying on manual post-parsing checks, the system will use a Pydantic model with a dynamic field validator. The `selected_folder` field will be validated at runtime against the list of folders allowed for the document's category, passed via the validation context.
- **Retry Loop with Feedback**: Implementation of a strict 3-attempt limit. Attempts 2 and 3 will include explicit feedback about the previous rejected response and the allowed list.
- **Termination**: If the 3rd attempt fails, throw a hard error and stop the pipeline.
- **Single Source of Truth for Mappings**: The allowed folder list for the validator will be derived programmatically from the `FOLDER_ROUTING` dictionary in `src/processing/routing/config.py`.

### the agent's Discretion
- No specific discretion areas listed in CONTEXT.md.

### Deferred Ideas (OUT OF SCOPE)
- No deferred ideas for this phase.

## Summary

The current routing implementation relies on a static Pydantic model (`RoutingResponse`) where the `selected_folder` is defined as a `str`. While the prompt provides the LLM with a list of allowed folders, the enforcement is performed manually via an `if selected in allowed_folders` check *after* Pydantic has already validated the response as a generic string. This creates a gap where the LLM can "hallucinate" folder names that look correct but do not exist in the configuration, leading to runtime failures or fallback to `13_others`.

**Primary recommendation:** Transition from manual post-parsing validation to structural validation by using a Pydantic model with a field validator that checks the selected folder against the category's allowed list at the moment of validation.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Schema Definition | API / Backend | — | The routing schema must be dynamic based on the category mapping in `config.py`. |
| Response Validation | API / Backend | — | Pydantic handles the structural enforcement via validators. |
| Retry Coordination | API / Backend | — | The `router.py` coordinates attempts and injects failure feedback into the prompt. |
| Mapping Truth | Config Layer | — | `FOLDER_ROUTING` in `config.py` is the sole source of allowed folders. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.x | Schema Validation | `@field_validator` and `info.context` allow for dynamic runtime enforcement. |

**Installation:**
No new packages required.

## Architecture Patterns

### Recommended Project Structure
The changes are localized to:
- `src/processing/routing/router.py`: Logic for the validator-based model and the feedback retry loop.
- `src/processing/routing/config.py`: (Reference only) Source of folder mappings.

### Pattern 1: Dynamic Schema Validation
**What:** Using a Pydantic model with a dynamic field validator to enforce a runtime-defined list of allowed values.
**When to use:** When the set of allowed values for a field changes based on runtime data (e.g., document category).
**Example:**
```python
from pydantic import BaseModel, field_validator

class RoutingResponse(BaseModel):
    selected_folder: str
    reason: str

    @field_validator('selected_folder')
    @classmethod
    def validate_folder(cls, v, info):
        # allowed_folders would be passed via validation context
        allowed = info.context.get('allowed_folders', [])
        if v not in allowed:
            raise ValueError(f"Invalid folder '{v}'. Must be one of: {', '.join(allowed)}")
        return v
```

### Anti-Patterns to Avoid
- **Post-Parsing Manual Checks:** Performing `if value in list` after Pydantic has already "validated" the field as a `str`. This defeats the purpose of using a schema for enforcement.
- **Dynamic Literal Attempt:** Trying to use `typing.Literal` with a dynamic list at runtime (e.g., `Literal[tuple(allowed)]`), which causes a `TypeError` in Python.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|----------------|-----------|
| JSON Validation | Custom regex/parser | Pydantic | Pydantic handles type coercion and complex validation natively and efficiently. |

## Common Pitfalls

### Pitfall 1: Static Literal Limitation
**What goes wrong:** Attempting to use `typing.Literal` with a dynamic list or tuple.
**Why it happens:** `Literal` requires static arguments defined at definition-time; it does not support runtime variables.
**How to avoid:** Use Pydantic's `@field_validator` and pass the allowed list via the validation context (`info.context`).

### Pitfall 2: Prompt-Schema Mismatch
**What goes wrong:** The prompt lists folders A and B, but the validator only allows A.
**Why it happens:** Desynchronization between the prompt string and the validator's allowed list.
**How to avoid:** Derive both the prompt's "Allowed Folders" section and the Pydantic validator's allowed list from the same list variable.

## Code Examples

### Dynamic Model Implementation
```python
from pydantic import BaseModel, field_validator

class RoutingResponse(BaseModel):
    selected_folder: str
    reason: str

    @field_validator('selected_folder')
    @classmethod
    def validate_folder(cls, v, info):
        allowed = info.context.get('allowed_folders', [])
        if v not in allowed:
            raise ValueError(f"Invalid folder '{v}'. Must be one of: {', '.join(allowed)}")
        return v

# Usage:
# model = RoutingResponse.model_validate(json_data, context={'allowed_folders': ['folder1', 'folder2']})
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Pydantic v2's `info.context` is supported by the current implementation. | Standard Stack | If not, we'll need to pass the allowed list through a different mechanism. |

## Open Questions (RESOLVED)

1. **Feedback Loop Detail**
   - What we know: We need to tell the LLM its previous choice was rejected.
   - What's unclear: Should we provide the exact Pydantic error message or a simplified "Not in allowed list" message?
   - Recommendation: Use a simplified, human-readable message to avoid confusing the LLM with internal Pydantic tracebacks.
   - **Status: RESOLVED** (Will use simplified messages).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Quick run command | `pytest tests/test_routing.py` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| SCHM-01 | RoutingResponse rejects folders not in the category's allowed list | unit | `pytest tests/test_routing.py::test_dynamic_schema_enforcement` |

### Wave 0 Gaps
- [ ] `tests/test_routing_schema.py` — Needs to be created to verify that the validator correctly raises `ValidationError` for invalid folders.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V5 Input Validation | yes | Pydantic validator enforcement for LLM outputs. |

### Known Threat Patterns for Python

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt Injection | Tampering | Strict output schema enforcement prevents the LLM from returning arbitrary commands or unexpected data structures. |
