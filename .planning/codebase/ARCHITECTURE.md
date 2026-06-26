---
last_mapped_commit: HEAD
---
# Architecture

**Focus:** arch
**Date:** 2026-06-26

## System Design
The system is a CLI-based pipeline for ingesting, categorizing, and organizing PDF documents using Vision and Text LLMs.

### Core Data Flow
1. **Ingestion**: `src/main.py` -> `src/pipeline.py` -> `src/ingest.py`. PDF pages are extracted as images.
2. **Vision Extraction (Pass 1)**: Pages are classified by LLMs (local or cloud) to extract Category, Resident, Date, and Summary. Extensive JSON caching (`SimpleCache`) ensures rate limit resilience.
3. **Timeline Grouping (Pass 2)**: Extracted page data is audited, dates interpolated, and semantic grouping is performed in `src/pipeline.py` based on timeline logic.
4. **Organization**: `src/organizer.py` takes grouped documents and handles final file structuring and output generation.

## Key Abstractions
- **`Pipeline`** (`src/pipeline.py`): Orchestrates the 2-pass processing logic.
- **`SimpleCache`** (`src/pipeline.py`): Atomic file-based JSON cache for LLM results.
- **`GemmaClient`** (`src/llm.py`): Wrapper for interacting with Gemini/Local LLMs with rate limit and fallback handling.
- **Schemas** (`src/schemas.py`): `PageClassification`, `DocumentGroup` enforce data consistency.
