<!-- GSD:project-start source:PROJECT.md -->

## Project

**File Categorizer Generalization**

A high-precision document processing pipeline that currently ingests housing-related PDFs and categorizes them. We are transforming it into a general-purpose, configuration-driven tool where users can provide their own instructions for AI extraction, cleaning, grouping, and folder organization via a config file.

**Core Value:** Empower users to seamlessly categorize and organize any type of PDF by simply providing clear AI instructions and destination folders, without changing the underlying pipeline engine.

### Constraints

- **Compatibility**: Must not alter the underlying Python architecture/pipeline logic.
- **Configuration**: Uses YAML/JSON for the config file.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages & Runtimes

- **Python**: Version 3.10+. Primary language for the categorization pipeline.

## Core Frameworks & Dependencies

- **PyMuPDF**: PDF manipulation, splitting, and rendering.
- **Pydantic**: Data validation and structured schemas (likely used with LLM outputs).
- **Tenacity**: Retry logic for robust API calls.
- **Google GenAI / OpenAI**: LLM integration for page classification and entity extraction.
- **Python-dotenv**: Managing environment variables (`.env`).

## Build & Tooling

- **Virtual Environments**: `venv` is used for isolation.
- **Type Checking**: `mypy` is used (evident from `.mypy_cache`).

## Configuration

- Environment variables are defined in `.env` (with an example provided in `.env.example`).
- API keys like `GEMINI_API_KEY` are managed via the environment.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Code Style & Patterns

- **Typing**: Type hints are heavily used (e.g., `list[tuple[int, PageClassification]]`, `Optional[Any]`).
- **Data Validation**: Pydantic is used for structured data models in `schemas.py`.
- **Modularity**: Code is split into focused modules (ingest, llm, pipeline, organizer, extractors, split).
- **Logging**: Python's standard `logging` library is used extensively to track pipeline progression (e.g., `logger.info(f"Starting Pass 1...")`).

## Error Handling

- Custom exceptions are used to signal specific failure states (e.g., `LLMFailureError`, `InvalidResponseError` in `llm.py`).
- Tenacity is employed for retry logic on flaky API calls (configured in `llm.py` or `providers.py`).
- Defensive checks exist to abort processing gracefully rather than losing data (e.g., throwing `RuntimeError` if page loss is detected during extraction).

## Naming

- Python standards apply (snake_case for variables/functions, PascalCase for classes).
- Specific module files prefix tests with `test_` for pytest compatibility.

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Pattern & Layers

## Data Flow

## Abstractions

- `PageClassification`: Data schema representing a single page's metadata (category, date, residents).
- `DocumentGroup`: Data schema representing a contiguous sequence of pages logically belonging together.
- `LLMClient`: Wrapper around LLM APIs to isolate the core logic from specific provider implementations.

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
