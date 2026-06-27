# Phase 04 Context: Audit & Fix

## Domain
Audit code for bugs and fix them, establishing a clean and stable foundation for upcoming testing.

## Decisions
- **Audit Scope**: Comprehensive. The audit will cover the entire codebase, including PDF parsing, pipeline logic, and recent cloud LLM integrations.
- **Error Handling**: Fail Fast. The pipeline must crash immediately upon encountering unexpected errors or malformed data to prevent propagation of bad state.
- **Bug Priority**: Code Smells & Structure. The primary focus of fixes will be on refactoring, improving type hinting, and ensuring structural cleanliness.

## Canonical Refs
- [.planning/ROADMAP.md](../../ROADMAP.md)
- [.planning/REQUIREMENTS.md](../../REQUIREMENTS.md)
- [.planning/PROJECT.md](../../PROJECT.md)

## Code Context
- **Reusable assets**: `src/schemas.py` (for Pydantic structure validation), `src/pipeline.py` (core orchestration).
- **Integration points**: The audit will touch all main stages (`ingest.py`, `pipeline.py`, `llm.py`, `organizer.py`).
