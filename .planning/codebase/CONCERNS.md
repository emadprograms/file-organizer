# Concerns

**Focus:** concerns
**Date:** 2026-07-01

## Known Issues & Tech Debt
- **LLM Dependency and Latency**: The architecture heavily relies on LLMs for page categorization and semantic grouping. This introduces inherent latency (e.g., delays added between page API calls) and reliability issues (hallucinations/failures), requiring robust retry logic which is complex to manage perfectly.
- **Memory Consumption for Large PDFs**: The process converts PDF pages to images and caches them in memory/JSON, which could scale poorly with massive documents causing Out of Memory (OOM) issues or excessive disk IO for the cache file.

## Fragile Areas
- **Date Interpolation Logic**: Pass 1.5 logic to interpolate missing dates (`_interpolate_dates`) is sensitive to edge cases where large blocks of pages are missing dates or where chronological order might legitimately be broken.
- **Tenant Grouping (Pass 2)**: Overwriting logic when tenant timelines overlap is a complex set of heuristics. When timelines naturally clash, determining the "winning" tenant is error-prone.

## Security Considerations
- **API Key Exposure**: The `GEMINI_API_KEY` is needed for functionality. Any accidental logging of environment variables or API payloads could leak this key.
- **PII Handling**: The application processes sensitive housing documents containing names (and possibly other PII). Sending raw images or text to external APIs like Google Gemini/OpenAI must be done under compliant organizational policies (data privacy risk).
