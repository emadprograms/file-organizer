# Codebase Structure

**Analysis Date:** 2026-07-07

## Directory Layout

```
[project-root]/
├── src/                    # Source code
│   ├── core/               # Shared schemas, config, and utility logic
│   ├── llm/                # LLM provider abstractions and orchestration
│   ├── processing/         # Document grouping, routing, and pipeline logic
│   ├── cleaning.py         # Pass 1: Data standardization and tenant resolution
│   ├── fs_utils.py         # File system operations (e.g., atomic writes)
│   ├── llm_client.py       # High-level LLM interaction wrapper
│   ├── logger.py           # Centralized logging system
│   └── organize.py         # Main CLI entry point
├── tests/                  # Comprehensive test suite
│   ├── fixtures/           # Sample data for testing
│   └── test_*.py           # Unit and integration tests
├── pdfs/                   # Input/Output PDF storage (project specific)
└── .env                    # Environment configuration (secrets)
```

## Directory Purposes

**src/core:**
- Purpose: Domain-wide constants, data models, and basic utilities.
- Contains: Pydantic schemas, configuration loaders, and a simple JSON cache.
- Key files: `schemas.py`, `config.py`, `cache.py`.

**src/llm:**
- Purpose: Abstracting the complexity of multiple LLM APIs.
- Contains: Provider implementations (Gemini, Groq, OpenRouter) and a central orchestrator.
- Key files: `llm.py`, `providers.py`.

**src/processing:**
- Purpose: The "brain" of the organization process.
- Contains: Logic for splitting pages into documents and assigning them to folders.
- Key files: `pipeline.py`, `grouping.py`, `routing.py`, `organizer.py`.

## Key File Locations

**Entry Points:**
- `src/organize.py`: The main script to run the organization process.

**Configuration:**
- `.env`: Primary secret storage.
- `src/core/config.py`: Application settings and constants.

**Core Logic:**
- `src/processing/pipeline.py`: Orchestrates the flow of data.
- `src/llm/llm.py`: Handles the resilient API communication.

**Testing:**
- `tests/`: All test files are located here, organized by component.

## Naming Conventions

**Files:**
- `snake_case.py`: Standard Python naming for all modules.
- `test_*.py`: Test files following pytest conventions.

**Directories:**
- `snake_case`: Standard directory naming.

## Where to Add New Code

**New Feature (Processing Logic):**
- Primary code: `src/processing/`
- Tests: `tests/test_processing_*.py`

**New LLM Provider:**
- Implementation: `src/llm/providers.py` (create a new `LLMProvider` subclass).
- Tests: `tests/test_providers.py`

**New Data Schema:**
- Implementation: `src/core/schemas.py`

**Utilities:**
- Shared helpers: `src/core/utils.py` or `src/fs_utils.py`.

## Special Directories

**pdfs/:**
- Purpose: Contains input PDFs and the output of the categorized process.
- Generated: Yes.
- Committed: No (usually ignored in git).

---

*Structure analysis: 2026-07-07*
