# External Integrations

**Focus:** tech
**Date:** 2026-07-01

## APIs & Third-party Services
- **Google Gemini API**: Utilized for vision-first page classification and extracting structured information (like residents and dates) via the `google-genai` SDK. Requires `GEMINI_API_KEY`.
- **OpenAI API**: Likely used as an alternative or supplementary LLM provider for semantic tasks or resident mapping via the `openai` Python SDK.

## Storage
- **File System**: Local filesystem is used for reading input PDFs and writing processed/split PDFs into a structured `./output` directory hierarchy.
- No external databases appear to be used; the system relies on LLMs for processing and the file system for structured output.
