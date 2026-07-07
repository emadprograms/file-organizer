# External Integrations

**Date:** 2026-07-07

## APIs & LLMs
The application extensively relies on external Large Language Model APIs for intelligent document processing, entity extraction, routing, and cleaning.

- **Google Gemini API**: 
  - Accessed via the official `google-genai` SDK.
  - Used as the primary model endpoint (e.g., `gemini-2.5-flash`, `gemini-3.5-flash`) for structured JSON generation.
- **OpenRouter API**:
  - Accessed by configuring the `openai` Python SDK with OpenRouter's base URL (`https://openrouter.ai/api/v1`).
  - Allows routing to a variety of OSS and proprietary models (e.g., `google/gemma-4-26b-a4b-it`).
- **Groq API**:
  - Accessed by configuring the `openai` Python SDK with Groq's OpenAI-compatible endpoint (`https://api.groq.com/openai/v1`).
  - Provides fast inference model options (e.g., `qwen/qwen3.6-27b`).

## Databases
- None. The application operates as a batch script and uses the local filesystem for its input (PDF files), processing state (`checkpoints/` directory), and output (JSON reports and categorized PDFs).

## Auth Providers
- None. The application does not involve end-user authentication. API access to LLMs is managed via standard API keys in `.env`.

## Webhooks & Events
- None. The application does not expose external webhooks or listen for external events; it is invoked manually via its CLI entry point.
