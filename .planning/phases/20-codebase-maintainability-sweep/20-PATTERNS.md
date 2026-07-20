# Phase 20: Codebase Maintainability Sweep - Patterns

This document defines the type hinting and docstring patterns to be applied across the v2.0 codebase modules to ensure maintainability, as per D-01, D-02, and D-03.

## 1. Domain Modules (`src/core/`, `src/llm/`, `src/utils/`)

**Files to modify:**
- `src/core/*.py`
- `src/llm/*.py`
- `src/utils/*.py`

**Role & Data Flow:**
- **Role:** Foundational infrastructure. Defines shared schemas (Pydantic models), utility functions, logging configurations, and LLM communication strategy.
- **Data Flow:** Consumed by all pipeline stages. `src/llm/llm.py` takes raw prompts/contents and returns parsed schemas via Pydantic models in `src/core/schemas.py`.

**Closest Analog:** `src/core/utils.py` (has partial docstrings, needs standardizing).

**Pattern / Code Excerpt:**
All methods, including private methods like `_route_llm_call`, must be thoroughly documented using Google-style docstrings, and modern `list` / `dict` typing must replace `typing.List` / `typing.Dict`.

```python
# Before (Legacy / Missing Docs)
def _route_llm_call(self, model: str, contents: list, response_schema: type | None = None, validation_context: dict | None = None, log_prefix: str = "Retry", max_attempts: Optional[int] = None) -> Any:
    """Route an LLM call through the provider with deterministic resilience and fallbacks."""
    # ...

# After (Modern Typing + Exhaustive Docstrings)
def _route_llm_call(
    self, 
    model: str, 
    contents: list[dict[str, Any]], 
    response_schema: type | None = None, 
    validation_context: dict[str, Any] | None = None, 
    log_prefix: str = "Retry", 
    max_attempts: int | None = None
) -> Any:
    """Route an LLM call through the provider with deterministic resilience and fallbacks.

    Handles rotation between providers, exponential backoffs, and tracking of request rates.
    This internal method ensures fail-safety without leaking exceptions unnecessarily.

    Args:
        model (str): The primary LLM model string to use (e.g., 'gemini-1.5-flash').
        contents (list[dict[str, Any]]): The messages payload to be routed to the LLM.
        response_schema (type | None): Optional Pydantic model type for structured output validation.
        validation_context (dict[str, Any] | None): Optional context dictionary for Pydantic field validators.
        log_prefix (str): Prefix used for log tracking (default: "Retry").
        max_attempts (int | None): Number of times to retry the primary model before fallback.

    Returns:
        Any: A validated Pydantic object if response_schema is provided, otherwise raw text/dict.
        
    Raises:
        ProviderRotationExhaustedError: If all configured models and fallbacks fail.
    """
```

## 2. Pipeline Logic Modules (`src/grouping/`, `src/routing/`, `src/timeline/`, `src/pdf/`, `src/tenant_config/`)

**Files to modify:**
- `src/grouping/*.py`
- `src/routing/*.py`
- `src/timeline/*.py`
- `src/pdf/*.py`
- `src/tenant_config/*.py`

**Role & Data Flow:**
- **Role:** Functional data pipeline processing stages. 
- **Data Flow:** Documents flow as Pydantic models (`DocumentGroup`, `ExtractedDocument`) sequentially through PDF extraction -> timeline -> grouping -> routing. Output of each stage is written to checkpoint JSONs.

**Closest Analog:** `src/routing/router.py` (functional pipeline stages processing domain objects).

**Pattern / Code Excerpt:**
Functions that modify or orchestrate state must specify specific generic types (e.g., `list[DocumentGroup]`) instead of `Any` or `list`.

```python
# Before
def group_documents(documents: Any, config: Any) -> list:
    pass

# After
def group_documents(
    documents: list[ExtractedDocument], 
    config: dict[str, Any]
) -> list[DocumentGroup]:
    """Group extracted documents into logical sets based on heuristics and configured rules.

    Applies the semantic matching rules in the configuration to group disparate PDF pages
    or individual documents into coherent entity groups.

    Args:
        documents (list[ExtractedDocument]): Flat list of previously extracted documents.
        config (dict[str, Any]): Project or tenant-level configurations.

    Returns:
        list[DocumentGroup]: List of aggregated document groups containing the source documents.
    """
    pass
```

## 3. Orchestration & CLI (`src/main.py`, `src/pipeline/`)

**Files to modify:**
- `src/main.py`
- `src/pipeline/*.py`

**Role & Data Flow:**
- **Role:** CLI entry point and high-level orchestration pipeline.
- **Data Flow:** Receives CLI args, loads tenant configurations, initializes `LLMClient`, and calls the functional pipeline domains in sequence, saving intermediary state to `.tracking/`.

**Closest Analog:** `src/pipeline/pipeline.py`.

**Pattern / Code Excerpt:**
Typing must be applied to main coordinator functions with appropriate complex typings where needed (like returning a tuple of statuses). 

```python
# Before
def run_pipeline(source_dir, output_dir, limit=None):
    pass

# After
def run_pipeline(
    source_dir: str, 
    output_dir: str, 
    limit: int | None = None
) -> dict[str, int]:
    """Execute the main document organization pipeline.

    Coordinates extraction, grouping, and routing of files from the source directory.
    Maintains checkpoint state in the output directory to allow resuming.

    Args:
        source_dir (str): Absolute or relative path to the unorganized documents.
        output_dir (str): Absolute or relative path to the target folder structure.
        limit (int | None): Optional limit on the number of documents to process in this run.

    Returns:
        dict[str, int]: Execution statistics (e.g., {"processed": 10, "failed": 2}).
        
    Raises:
        PipelineHaltError: If a fatal stage failure prevents pipeline continuation.
    """
```

## 4. Test Suites (`tests/`)

**Files to modify:**
- `tests/*.py`

**Role & Data Flow:**
- **Role:** Assuring functional correctness of the modules.
- **Data Flow:** Feeds mocked JSON data / Pytest fixtures into domain logic methods and asserts outputs.

**Closest Analog:** `tests/test_routing_router.py`.

**Pattern / Code Excerpt:**
Test files also receive type hints, specifically on fixtures and mock objects, to ensure that test maintainability remains high. Tests should have docstrings explaining the scenario and expected outcome.

```python
# Before
def test_double_check_others_agrees():
    client = MockLLMClient(["Finance", ("Finance", "Matches rules")])
    group = DocumentGroup(id="1")
    assert double_check_others(group, client) == "Finance"

# After
def test_double_check_others_agrees() -> None:
    """Test that the double-check routing successfully returns the folder if LLM agrees twice.
    
    Verifies that the `double_check_others` escape hatch resolves correctly when the
    primary and secondary validation pass yield identical folder assignments.
    """
    client: MockLLMClient = MockLLMClient(["Finance", ("Finance", "Matches rules")])
    group: DocumentGroup = DocumentGroup(id="1")
    
    result: str = double_check_others(group, client)
    
    assert result == "Finance"
```
