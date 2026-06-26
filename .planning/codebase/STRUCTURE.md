---
last_mapped_commit: HEAD
---
# Directory Structure

**Focus:** arch
**Date:** 2026-06-26

## Core Layout
- `src/`: Core application logic
  - `main.py`: Entry point and CLI parsing
  - `pipeline.py`: The two-pass categorization engine
  - `llm.py`: API wrappers and AI clients
  - `ingest.py`: PDF handling
  - `organizer.py`: File output structuring
  - `schemas.py`: Pydantic definitions
  - `split.py`: PDF splitting utilities
- `scripts/`: Standalone utilities and local evaluation tools (`evaluate_local.py`, `compress_pdf.py`, etc.)
- `tests/`: Pytest suites
- `pdfs/`, `output/`, `scratch/`: Assumed data and output directories

## File Naming Conventions
- Standard Python `snake_case` for module names.
- `.planning/` directory used for GSD planning and codebase maps.
