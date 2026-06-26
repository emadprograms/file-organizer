---
last_mapped_commit: HEAD
---
# Tech Stack

**Focus:** tech
**Date:** 2026-06-26

## Core Technologies
- **Language**: Python 3
- **Primary Domain**: Document processing (PDF) and LLM-based categorization

## Key Dependencies
- `PyMuPDF`: PDF parsing and image extraction
- `google-genai`, `openai`: Cloud LLM inference
- `pydantic`: Schema validation and structured data (`src/schemas.py`)
- `tenacity`: Retry logic for LLM calls
- `python-dotenv`: Environment variable management
- `pytest`: Testing framework

## Configuration
- Project relies on `.env` (e.g., `GEMINI_API_KEYS`, `USE_LOCAL_LLM`).
- CLI Arguments (e.g., `--no-local` fallback flags in `src/main.py`).
