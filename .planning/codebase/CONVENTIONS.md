# Coding Conventions and Architectural Patterns

This document outlines the coding standards, design patterns, conventions, and quality standards enforced across the `file-organizer` codebase.

---

## 1. Language & Runtime Standards

- **Python Version**: Python 3.12+
- **Type Annotations**:
  - Modern Python built-in generic collections must be used directly (`list`, `dict`, `set`, `tuple`) per PEP 585. Legacy `typing.List`, `typing.Dict`, `typing.Set`, and `typing.Tuple` are **strictly forbidden** and enforced via automated AST compliance tests ([`tests/test_type_hint_compliance.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_type_hint_compliance.py)).
  - Union types should use the modern `|` syntax (e.g., `str | None`, `Path | str`, `int | float`) per PEP 604.
  - Standard `typing` imports allowed: `Optional`, `Any`, `Protocol`, `Generator`, `Callable`, `TypeVar`.
  - All public functions, class methods, and module exports should have explicit parameter types and return type annotations.

---

## 2. Code Organization & Layered Architecture

The codebase follows a modular, layered architecture located under `src/`:

```
src/
├── core/             # Base configurations, schemas, exceptions, state, models, and indexing
├── categorization/   # Page classification and fine-grained categorization logic
├── grouping/         # Boundary detection and multi-page document grouping algorithms
├── routing/          # Folder routing rules, LLM-based categorization, and escape hatches
├── timeline/         # Arabic/Hijri date parsing, name clustering, and timeline reconciliation
├── tenant_config/    # Tenant YAML configuration loaders and timeline parsers
├── llm/              # LLM client orchestration, provider strategies (Gemini, OpenRouter, Groq), and mock fallbacks
├── inbox/            # Incoming document parsing and filename command resolver
├── watcher/          # File system UI watcher, lock files, and event orchestrator
├── reconcile/        # Reconciliation engine, duplicate detection, and ghost shortcut recovery
├── presentation/     # UI rendering and rich terminal output
├── pdf/              # PDF splitting, compression, extraction, and OpenCV image preprocessing
├── migration/        # Schema migration and legacy report conversions
├── utils/            # Atomic file operations, logger initialization, and shortcut manipulation
└── main.py           # CLI entry point (subcommands: create, reconcile, migrate, watcher)
```

### Architectural Separation Rules
1. **Core Independence**: `src/core/` must never contain UI or presentation logic. Terminal formatting resides exclusively in `src/presentation/` (enforced via [`tests/test_architecture_phase25.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_architecture_phase25.py)).
2. **Explicit Entry Points**: Each subsystem provides an `__init__.py` exposing only its intended public interface.
3. **Decoupled LLM Strategies**: Core business logic interacts with `LLMClient` or `LLMProvider` protocols rather than direct third-party SDK clients.

---

## 3. Data Validation & Modeling (Pydantic v2)

The codebase relies on **Pydantic v2** (`BaseModel`, `Field`, `field_validator`, `ValidationInfo`) for data structures, schema validation, and structured LLM response parsing:

- **Schema Definition**:
  - Fields must declare explicit types, default values or factory functions (`default_factory=list`), and clear descriptions.
  - Use `validation_alias=AliasChoices(...)` to handle non-deterministic LLM JSON keys gracefully (e.g. `AliasChoices('brief_arabic_title', 'title', 'arabic_title')`).
- **Validation Context**:
  - Dynamic constraints (such as runtime-allowed folder lists) should be passed into Pydantic models via `ValidationInfo.context` and validated within `@field_validator` classmethods.
- **Pre-Validation Sanitization**:
  - Non-standard inputs (such as boolean strings `"true"` / `"false"` from LLM output) should use `mode='before'` validators to clean inputs before schema assignment.

Example pattern from [`src/core/schemas.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/schemas.py):
```python
class RoutingResponse(BaseModel):
    reason: str = Field(
        validation_alias=AliasChoices('reason', 'reasoning'),
        description="Explanation of why this folder was selected"
    )
    selected_folder: str = Field(description="The exact name of the selected folder from the allowed list")

    @field_validator('selected_folder')
    @classmethod
    def validate_folder(cls, v: str, info: ValidationInfo) -> str:
        allowed = info.context.get('allowed_folders', []) if info.context else []
        if v not in allowed:
            raise ValueError(f"Selected folder '{v}' is not in the allowed list: {allowed}")
        return v
```

---

## 4. Error Handling & Exception Hierarchy

All custom application exceptions inherit from `FileOrganizerError` defined in [`src/core/exceptions.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/exceptions.py):

```
FileOrganizerError (Base Exception)
├── PipelineHaltError (Critical error requiring full pipeline halt)
│   ├── RoutingValidationError (LLM failed to select a valid folder after retries)
│   └── LLMFailureError (Unrecoverable API error or authentication failure)
├── ConfigurationError (Missing or invalid YAML/environment configuration)
├── ValidationError (Validation checks or data schema failures)
├── ProviderRotationExhaustedError (All LLM providers and fallbacks failed)
└── GracefulHaltException (Clean stop signal allowing state persistence)
```

### Conventions:
1. **Explicit Error Chaining**: Always chain unexpected underlying exceptions using `raise CustomError(...) from e`.
2. **Fail-Fast vs. Graceful Resilience**:
   - Authentication (HTTP 401) or invalid configuration errors fail immediately with `LLMFailureError` / `ConfigurationError`.
   - Transient errors (HTTP 429 rate limits, schema validation failures) trigger bounded retries, provider fallback rotations, or graceful halting.
3. **State Persistence on Halt**: Functions performing batch processing must catch recoverable failures, persist current checkpoint state to disk, and raise `GracefulHaltException`.

---

## 5. Logging, Observability & Console Output

The logging architecture is managed via [`src/utils/logger.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/utils/logger.py).

### Canonical Logger Initialization
Every module across `src/` must initialize its logger using the canonical pattern (enforced by [`tests/test_utils_logger_audit.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_utils_logger_audit.py)):
```python
import logging

logger = logging.getLogger(f"file_organizer.{__name__}")
```

### Prohibited Standard `print()` Calls
Direct `print()` calls are strictly forbidden in `src/` (enforced by [`tests/test_utils_logger_audit.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_utils_logger_audit.py) and [`tests/test_utils_telemetry_audit.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_utils_telemetry_audit.py)).
- For user-facing terminal presentation, use `rich.console.Console` (`console.print(...)`) or `vprint(...)`.
- For diagnostic and operational messages, use `logger.info()`, `logger.debug()`, `logger.warning()`, or `logger.error()`.

### Dual Logging & Audit Tracing
When `setup_logging(run_id, verbose)` runs, it provisions a dedicated run directory under `logs/<timestamp>_<run_id>/` with three artifacts:
1. `app.log`: Human-readable plain text log for INFO and above.
2. `debug.log`: JSONL formatted detailed log for DEBUG and above with stack traces.
3. `traces.jsonl`: High-precision structured decision audit records emitted via `log_decision_trace(decision_type, payload)` for post-run verification.

---

## 6. File System & Windows OS Integration Patterns

Operating within a Windows environment with potential network drives, antivirus scanning, and OneDrive syncing requires specific file system patterns in [`src/utils/fs.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/utils/fs.py):

### Atomic File Writes
Always perform file updates using the `atomic_write` context manager. It writes to a temporary file (`<basename>.<uuid>.tmp`) and renames it with a 10-attempt retry loop to mitigate Windows file-locking race conditions:
```python
from src.utils.fs import atomic_write

with atomic_write(target_path) as tmp_path:
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
```

### Windows Shortcuts (`.lnk`)
- Shortcuts are manipulated via PowerShell COM interop ([`src/utils/windows_shortcut.ps1`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/utils/windows_shortcut.ps1)).
- Paths with `\\?\` UNC prefixes are automatically normalized prior to passing to `WScript.Shell`.
- For bulk operations, use `batch_create_shortcuts` and `batch_read_shortcut_targets` to invoke PowerShell in a single process rather than spawning multiple subprocesses.

### Safe Directory Merges & Path Sanitization
- Directory moves/merges must use `merge_and_remove_dir(src, dst)` to recursively move files, handle name collisions, and safely purge old directories.
- Arabic names and dates containing direction markers (e.g. `\u200e` LTR marks for date ranges like `(2002 - الآن)`) must be preserved and handled consistently when formatting directory names.

---

## 7. LLM Integration & Resilience Patterns

The LLM subsystem in [`src/llm/`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/llm/) enforces high availability and strict rate-limit management:

- **Strategy Pattern (`LLMProvider`)**:
  - `GeminiProvider`, `OpenRouterProvider`, and `GroqProvider` implement the `LLMProvider` protocol.
  - `MockLLMProvider` is provided for offline testing and `--skip-llm` CLI execution.
- **Model Fallback Rotation**:
  - Primary requests execute against the specified model (e.g., `gemini-3.5-flash`).
  - Upon unrecoverable failure or exhaustion, the client rotates through configured fallbacks: `["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash"]`.
- **Rate-Limiting & Cooldown**:
  - Inter-page request throttling is enforced via `delay_between_pages` (default 7.0s).
  - Rate limit errors (HTTP 429) trigger a 65-second cooldown via `activate_cooldown()` before continuing.

---

## 8. Naming Conventions & Style Guidelines

| Identifier Type | Convention | Example |
|---|---|---|
| Packages & Modules | `snake_case` | `fine_categorization.py`, `name_matcher.py` |
| Classes | `PascalCase` | `DocumentGroup`, `LLMClient`, `GroupingStateManager` |
| Functions & Methods | `snake_case` | `extract_pdf_segment`, `route_document` |
| Internal / Private Functions | `_snake_case` | `_route_llm_call`, `_write_jsonl_trace` |
| Constants & Enums | `UPPER_SNAKE_CASE` | `PROJECT_ROOT`, `FOLDER_ROUTING`, `SINGLE_MATCH` |
| Pydantic Model Fields | `snake_case` | `canonical_tenant`, `expected_house_number` |
| Test Functions | `test_<action>_<expected>` | `test_constrained_routing_success` |

All docstrings follow the Google/Sphinx format including multi-line summaries, `Args:`, `Returns:`, and `Raises:` sections.
