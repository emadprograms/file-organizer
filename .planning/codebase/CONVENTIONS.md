---
last_mapped_commit: HEAD
---
# Code Conventions

**Focus:** quality
**Date:** 2026-06-26

## Style & Syntax
- **Typing**: Extensive use of Python type hints (`typing.List`, `typing.Optional`, `Any`).
- **Data Models**: Pydantic `BaseModel` used for structured outputs and schemas.
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes.

## Patterns
- **Fallback Logic**: Heavily nested try-except blocks for graceful degradation from Cloud LLM to Local Vision/OCR.
- **Caching**: File-based caching (`.cache.json`) is integrated directly into the `Pipeline` to prevent re-processing identical PDF pages.
- **Concurrency**: `ThreadPoolExecutor` is used for parallel processing where applicable, though some caching involves `threading.Lock`.

## Error Handling
- Custom exceptions like `LLMFailureError` and `InvalidResponseError` in `src/llm.py`.
- Graceful output degradation (falling back to "UNKNOWN" residents or dates if extraction fails).
