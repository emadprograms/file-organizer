# Tech Stack

**Date:** 2026-07-07

## Languages
- **Python**: Primary language used across the entire codebase for CLI, PDF processing, and LLM orchestration.

## Runtime & Environment
- **Python Virtual Environment (`venv`)**: Standard virtual environment used for dependency isolation.
- **Configuration**: Uses `.env` files managed via `python-dotenv` and standard `os.getenv` for API keys and basic model configuration. No complex configuration frameworks are present.

## Frameworks & Libraries
- **Pydantic**: Extensive use for data validation, typing, and enforcing structured JSON schemas in LLM outputs.
- **Argparse**: Standard Python library utilized for building the CLI entry points (e.g., `organize.py`).
- **PyMuPDF (fitz)**: Core library used for PDF manipulation (reading page counts, splitting, organizing pages).
- **Tenacity**: Provides decorator-based retry logic for handling rate limits and transient errors from LLM providers.
- **RapidFuzz**: Rapid fuzzy string matching algorithm, used in data reconciliation and cleaning.
- **Rich**: Used for rich text and robust terminal visualization.
- **Hijridate**: Specialized library for Hijri (Islamic) date parsing and conversions.
- **Pytest**: Primary testing framework.
- **Google-GenAI & OpenAI**: SDKs for external LLM API interaction.

## Tooling
- **Logging**: Standard Python `logging` module configured for both application runtime logs and debugging logs.
