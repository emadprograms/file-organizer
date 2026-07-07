# Technology Stack

**Analysis Date:** 2026-07-07

## Languages

**Primary:**
- Python 3.12 - Core application logic, document processing pipeline, and LLM orchestration.

## Runtime

**Environment:**
- CPython 3.12.10

**Package Manager:**
- pip (via requirements.txt)
- Lockfile: Not detected

## Frameworks

**Core:**
- Pydantic - Used for structured data schemas and LLM response validation (`src/core/schemas.py`).

**Testing:**
- pytest - Primary test runner used across the `tests/` directory.

**Build/Dev:**
- python-dotenv - Environment variable management.
- rich - Terminal formatting and logging.

## Key Dependencies

**Critical:**
- google-genai - Integration with Google Gemini LLMs.
- openai - Integration with OpenAI-compatible APIs (OpenRouter, Groq).
- PyMuPDF (fitz) - PDF manipulation, reading, and splitting (`src/organize.py`).
- tenacity - Robust retry logic for API calls.

**Infrastructure:**
- rapidfuzz - Fast string matching for name clustering (`src/llm/llm.py`).
- PyYAML - Configuration file parsing.
- hijridate - Handling Hijri dates in document processing.

## Configuration

**Environment:**
- `.env` file for API keys (e.g., `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`).

**Build:**
- No complex build system detected; standard Python source distribution.

## Platform Requirements

**Development:**
- Python 3.12+
- API Keys for Google Gemini, OpenRouter, or Groq.

**Production:**
- Linux/Windows environment with access to PDF files and LLM APIs.

---

*Stack analysis: 2026-07-07*
