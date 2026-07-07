# Codebase Conventions

**Date**: 2026-07-07

## 1. Code Style & Formatting
- **Language**: Python 3.
- **Type Hinting**: Pervasive use of type hints (e.g., `str`, `Optional[int]`, `list[DocumentGroup]`) using the `typing` module and built-in generics to ensure clarity and support IDE auto-completion.
- **Docstrings**: Google-style docstrings are used for functions, classes, and modules, clearly defining `Args:`, `Returns:`, and providing robust behavioral descriptions.
- **Linting & Formatting**: No strict enforcing configuration (like `pyproject.toml` with `ruff` or `black`, or `.flake8`) is present at the root, but the code adheres to standard PEP 8 spacing and stylistic guidelines manually.

## 2. Naming Conventions
- **Variables and Functions**: `snake_case` (e.g., `sanitize_filename`, `parse_datetime_str`).
- **Classes**: `PascalCase` (e.g., `LLMClient`, `GeminiProvider`, `Pipeline`).
- **Constants/Globals**: `UPPER_SNAKE_CASE` (e.g., `OPENROUTER_MODEL`).
- **Private Modifiers**: Internal class methods and state variables are prefixed with an underscore (e.g., `_route_llm_call`, `_fallback_toggle`).

## 3. Architecture & Patterns
- **Separation of Concerns**: The codebase is logically divided into domains under `src/`:
  - `core/`: Schemas (Pydantic-like or simple objects), configuration, and pure utility functions (`utils.py`).
  - `llm/`: Provider interfaces and the resilient `LLMClient`.
  - `processing/`: Domain logic for the document pipeline (grouping, routing, organizing, visualizer).
- **Strategy Pattern**: LLM providers are implemented using a common `LLMProvider` interface, allowing `LLMClient` to transparently swap between `GeminiProvider`, `OpenRouterProvider`, and `GroqProvider`.
- **Pipeline Orchestration**: The system operates on a multi-pass pipeline architecture (cleaning -> grouping -> routing -> physical file generation). Data is persisted as checkpoints (`*_cleaned.json`, `*_grouped.json`) between passes to support resume capabilities.
- **Resiliency & Failover**: Network calls to LLMs implement robust fallback patterns. If one provider fails (e.g., 429 Rate Limit or 5xx Server Error), the client gracefully falls back to secondary providers with thread-safe toggles and exponential backoffs.

## 4. Error Handling
- **Custom Exceptions**: Uses specific domain exceptions for expected failure modes, such as `LLMFailureError` and `InvalidResponseError`.
- **Graceful Degradation**: The orchestrator prefers logging warnings and failing over to alternative mechanisms rather than immediately crashing on API failures.
- **CLI Validation**: Scripts meant to be run directly (like `organize.py`) validate the environment and input directories early, printing clear error messages to `sys.stderr` and exiting with a non-zero code (`sys.exit(1)`) rather than throwing unhandled stack traces.
- **Trace Logging**: Interactions and errors with LLMs are dumped to JSON trace files in a `.tracking`/`logs` or `logs/` directory for later debugging.
