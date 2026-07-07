# External Integrations

**Analysis Date:** 2026-07-07

## APIs & External Services

**LLM Providers:**
- Google Gemini - Primary LLM for classification and grouping.
  - SDK: `google-genai`
  - Auth: `GEMINI_API_KEY`
- OpenRouter - Failover LLM provider.
  - SDK: `openai` (compatible)
  - Auth: `OPENROUTER_API_KEY`
- Groq - Failover LLM provider.
  - SDK: `openai` (compatible)
  - Auth: `GROQ_API_KEY`

## Data Storage

**Databases:**
- Not detected. The application uses local JSON files for caching and checkpoints.

**File Storage:**
- Local filesystem: Used for reading input PDFs, writing categorized PDFs, and storing reports/logs.

**Caching:**
- Local JSON files: Simple cache implementation (`src/core/cache.py`) to avoid redundant API calls.

## Authentication & Identity

**Auth Provider:**
- API Key based authentication for all external LLM services.

## Monitoring & Observability

**Error Tracking:**
- Not detected.

**Logs:**
- Custom logging system (`src/logger.py`) that writes to local files and provides verbose console output.
- Trace logging: Detailed JSON traces of LLM requests/responses are stored in `logs/traces/` (`src/llm/llm.py`).

## CI/CD & Deployment

**Hosting:**
- Not detected. Designed as a CLI tool for local execution.

**CI Pipeline:**
- Not detected.

## Environment Configuration

**Required env vars:**
- `GEMINI_API_KEY` (Required)
- `OPENROUTER_API_KEY` (Optional)
- `GROQ_API_KEY` (Optional)

**Secrets location:**
- `.env` file.

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

---

*Integration audit: 2026-07-07*
