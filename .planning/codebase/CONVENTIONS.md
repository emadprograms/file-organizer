# Coding Conventions

**Analysis Date:** 2026-07-07

## Naming Patterns

**Files:**
- `snake_case.py`: All source files use lowercase with underscores.

**Functions:**
- `snake_case`: Standard Python function naming.

**Variables:**
- `snake_case`: Local variables and parameters use lowercase with underscores.

**Types:**
- `PascalCase`: Pydantic models and classes use PascalCase (e.g., `DocumentGroup` in `src/core/schemas.py`).

## Code Style

**Formatting:**
- Standard PEP 8 style observed. No explicit formatter configuration (like `.prettierrc` or `pyproject.toml` with black/ruff) was detected, but the code is consistently formatted.

**Linting:**
- Not detected.

## Import Organization

**Order:**
1. Standard library imports.
2. Third-party imports (e.g., `pydantic`, `google.genai`).
3. Local module imports (starting with `src.`).

**Path Aliases:**
- The `src` directory is added to `sys.path` in `src/organize.py` to allow absolute imports from the root.

## Error Handling

**Patterns:**
- **Custom Exceptions:** Use of specific exception classes for LLM failures (`LLMFailureError`, `InvalidResponseError` in `src/llm/llm.py`).
- **Resilient Routing:** Wrapping API calls in a try-except block with automatic failover to alternative providers.
- **Atomic File Operations:** Writing to temporary files before renaming to prevent data loss during crashes.

## Logging

**Framework:** `logging` (Standard Library).

**Patterns:**
- Centralized configuration in `src/logger.py`.
- Use of a "file_organizer" named logger.
- Dual logging: Console output for user feedback and file output for auditing.
- Trace logging: JSON dumps of LLM requests and responses stored in `logs/traces/`.

## Comments

**When to Comment:**
- Module-level docstrings describe the purpose of the file.
- Complex logic (e.g., the failover loop in `src/llm/llm.py`) is documented with inline comments.

**JSDoc/TSDoc:**
- Not applicable (Python).

## Function Design

**Size:** Functions are generally focused, though the main LLM routing loop in `src/llm/llm.py` is relatively large to handle all edge cases of API failure.

**Parameters:** Type hinting is used consistently for function signatures.

**Return Values:** Pydantic models are used for structured return values from LLM-related functions.

## Module Design

**Exports:** Modules export classes and functions. `__init__.py` files are present but generally empty.

**Barrel Files:** Not used.

---

*Convention analysis: 2026-07-07*
