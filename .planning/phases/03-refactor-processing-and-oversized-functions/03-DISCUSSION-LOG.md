# Phase 03: Refactor Processing and Oversized Functions - Discussion Log

**Date:** 2026-07-08

## Areas Discussed

### 1. Module Structure
- **Options presented:** Sub-packages vs flat sibling files.
- **Selection:** Break them into sub-packages (e.g., `src/processing/routing/`) for better isolation.
- **Notes:** None.

### 2. LLM Layer Scope
- **Options presented:** Include refactoring vs defer it.
- **Selection:** Yes, include it. We should fix the hardcoded rate limits and mock logic now.
- **Notes:** None.

### 3. Exception Strategy
- **Options presented:** Custom exception hierarchy vs built-in exceptions.
- **Selection:** You decide.
- **Agent Discretion:** Decided to implement a custom exception hierarchy (e.g., `FileOrganizerError`, `ConfigurationError`) for cleaner pipeline error handling.

### 4. Pillow Dependency
- **Options presented:** Add to requirements.txt vs PyMuPDF-only compression.
- **Selection:** I believe pymupdf comopression is better but if it is not. then add pillow to requirements.txt. you decide.
- **Agent Discretion:** Decided to use PyMuPDF-only compression to remove the external dependency entirely.

---
*Note: This log is for human reference. Downstream agents consume CONTEXT.md.*
