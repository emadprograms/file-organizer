# Directory Structure

**Focus:** arch
**Date:** 2026-07-01

## Layout
- `/src`: Contains the core application logic.
  - `main.py`: The command-line entry point.
  - `pipeline.py`: The central orchestrator for the multi-pass processing.
  - `organizer.py`: Logic for saving output files logically on disk.
  - `extractors.py`: Heuristics and logic for parsing specific parts of documents (e.g., footers).
  - `llm.py`: Interfaces with the Google Gemini API for extraction.
  - `ingest.py`: PDF handling for reading and image extraction.
  - `split.py`: PDF slicing and generation.
  - `schemas.py`: Pydantic data models (`PageClassification`, `DocumentGroup`).
  - `config.py`: Environment and logging setup.
  - `cache.py`: Simple caching layer for caching API results during processing.
- `/tests`: Contains unit and integration tests.
- `/docs`: Contains documentation.
- `/output`: The default target directory where categorized and organized PDFs are saved.

## Naming Conventions
- Modules are named in lowercase (`main.py`, `pipeline.py`).
- Classes use PascalCase (`FileOrganizer`, `Pipeline`, `PageClassification`).
- Functions and methods use snake_case (`process_pdf`, `_interpolate_dates`).
- Output files follow structured patterns (e.g., `{Date}_{Category}.pdf`).
