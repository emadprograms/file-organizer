# Tech Stack

**Focus:** tech
**Date:** 2026-07-01

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
