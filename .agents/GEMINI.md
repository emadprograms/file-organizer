<!-- GSD:project-start source:PROJECT.md -->

## Project

**File Organizer Refactoring**

A technical debt cleanup and refactoring effort for the file organizer project. The goal is to remove unused legacy code by tracing imports from the main entry point, and to break down bloated functions and files into smaller, more focused modules to improve maintainability.

**Core Value:** Keep the codebase lean and maintainable without altering the existing correct functionality.

### Constraints

- **Functional Parity**: The refactoring must not break existing functionality or change the output format.
- **Maintainability**: The new modules should have clear, single responsibilities.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.12 - Core application logic, document processing pipeline, and LLM orchestration.

## Runtime

- CPython 3.12.10
- pip (via requirements.txt)
- Lockfile: Not detected

## Frameworks

- Pydantic - Used for structured data schemas and LLM response validation (`src/core/schemas.py`).
- pytest - Primary test runner used across the `tests/` directory.
- python-dotenv - Environment variable management.
- rich - Terminal formatting and logging.

## Key Dependencies

- google-genai - Integration with Google Gemini LLMs.
- openai - Integration with OpenAI-compatible APIs (OpenRouter, Groq).
- PyMuPDF (fitz) - PDF manipulation, reading, and splitting (`src/organize.py`).
- tenacity - Robust retry logic for API calls.
- rapidfuzz - Fast string matching for name clustering (`src/llm/llm.py`).
- PyYAML - Configuration file parsing.
- hijridate - Handling Hijri dates in document processing.

## Configuration

- `.env` file for API keys (e.g., `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`).
- No complex build system detected; standard Python source distribution.

## Platform Requirements

- Python 3.12+
- API Keys for Google Gemini, OpenRouter, or Groq.
- Linux/Windows environment with access to PDF files and LLM APIs.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- `snake_case.py`: All source files use lowercase with underscores.
- `snake_case`: Standard Python function naming.
- `snake_case`: Local variables and parameters use lowercase with underscores.
- `PascalCase`: Pydantic models and classes use PascalCase (e.g., `DocumentGroup` in `src/core/schemas.py`).

## Code Style

- Standard PEP 8 style observed. No explicit formatter configuration (like `.prettierrc` or `pyproject.toml` with black/ruff) was detected, but the code is consistently formatted.
- Not detected.

## Import Organization

- The `src` directory is added to `sys.path` in `src/organize.py` to allow absolute imports from the root.

## Error Handling

- **Custom Exceptions:** Use of specific exception classes for LLM failures (`LLMFailureError`, `InvalidResponseError` in `src/llm/llm.py`).
- **Resilient Routing:** Wrapping API calls in a try-except block with automatic failover to alternative providers.
- **Atomic File Operations:** Writing to temporary files before renaming to prevent data loss during crashes.

## Logging

- Centralized configuration in `src/logger.py`.
- Use of a "file_organizer" named logger.
- Dual logging: Console output for user feedback and file output for auditing.
- Trace logging: JSON dumps of LLM requests and responses stored in `logs/traces/`.

## Comments

- Module-level docstrings describe the purpose of the file.
- Complex logic (e.g., the failover loop in `src/llm/llm.py`) is documented with inline comments.
- Not applicable (Python).

## Function Design

## Module Design

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| CLI Controller | Validates environment and coordinates the multi-pass pipeline | `src/organize.py` |
| Pipeline | Manages the flow from cleaning $ightarrow$ grouping $ightarrow$ routing | `src/processing/pipeline.py` |
| Cleaning Phase | Standardizes extracted data and resolves tenants | `src/cleaning.py` |
| Grouping Logic | Uses LLM to find boundaries between different documents | `src/processing/grouping.py` |
| Routing Logic | Assigns final folder paths to grouped documents | `src/processing/routing.py` |
| LLM Client | Orchestrates requests across Gemini, OpenRouter, and Groq with failover | `src/llm/llm.py` |
| Schemas | Defines Pydantic models for structured LLM I/O | `src/core/schemas.py` |
| Cache | Prevents redundant LLM calls using local JSON storage | `src/core/cache.py` |

## Pattern Overview

- **Multi-Pass Architecture:** Separates individual page classification (Pass 1) from document boundary detection (Pass 2).
- **Robust LLM Routing:** Implements a provider sequence with automatic failover and rate-limit cooldowns.
- **Structured I/O:** Heavily relies on Pydantic schemas to ensure LLM responses match expected data formats.
- **Checkpointing:** Saves intermediate results (`_cleaned.json`, `_grouped.json`) to allow resumption after failure.

## Layers

- Purpose: Shared utilities, configuration, and data models.
- Location: `src/core/`
- Contains: `schemas.py`, `config.py`, `cache.py`, `utils.py`.
- Depends on: Pydantic.
- Used by: All other layers.
- Purpose: Abstracting LLM provider details and providing resilient API access.
- Location: `src/llm/`
- Contains: `llm.py`, `providers.py`.
- Depends on: `google-genai`, `openai`.
- Used by: `src/processing/` and `src/cleaning.py`.
- Purpose: Implementing the domain logic for document organization.
- Location: `src/processing/`
- Contains: `pipeline.py`, `grouping.py`, `routing.py`, `organizer.py`.
- Depends on: `src/llm/`, `src/core/`.
- Used by: `src/organize.py`.

## Data Flow

### Primary Request Path

## Key Abstractions

- Purpose: A high-level wrapper for multiple LLM providers that handles retries, failovers, and structured output.
- Examples: `src/llm/llm.py`
- Pattern: Strategy Pattern (via `LLMProvider` subclasses).
- Purpose: Represents a cohesive set of pages that form a single document.
- Examples: `src/core/schemas.py`
- Pattern: Data Transfer Object (DTO).

## Entry Points

- Location: `src/organize.py`
- Triggers: Manual execution via `python src/organize.py [target_dir]`.
- Responsibilities: Environment validation, pipeline coordination, and final PDF generation.

## Architectural Constraints

- **API Rate Limits:** The pipeline is throttled by LLM API limits, necessitating the `delay_between_pages` and cooldown logic in `src/llm/llm.py`.
- **Sequential Processing:** Most stages are sequential, though some LLM calls use `ThreadPoolExecutor` for concurrency.
- **Local State:** The application is stateless between runs except for the local JSON checkpoints and cache.

## Error Handling

- **Provider Failover:** If Gemini fails, it tries OpenRouter, then Groq.
- **Atomic Writes:** Uses a temporary file pattern to prevent corrupting checkpoints (`src/fs_utils.py`).
- **Global Error Limit:** Aborts the pipeline if too many consecutive 500 errors occur.

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.agents/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
