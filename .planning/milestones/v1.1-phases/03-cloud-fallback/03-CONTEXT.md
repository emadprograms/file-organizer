# Phase 03 Context: Cloud Fallback

## Domain
Implement Gemini -> OpenRouter -> Groq chain for cloud fallback.

## Decisions
- **Fallback Triggers**: Hybrid approach. Retry on 429s (wait 65s), but fall back immediately to the next provider on 500 or 503 errors instead of waiting/retrying.
- **Model Selection**: On OpenRouter, use the `gemma-4-26b-a4b-it` model. On Groq, use the `qwen3.6-27b` model.
- **Fallback Logging**: Log fallback events to stdout only (e.g., "Failed over to OpenRouter"). Keep the JSON cache schema clean without adding provider metadata.

## Canonical Refs
- [.planning/ROADMAP.md](../../ROADMAP.md)
- [.planning/REQUIREMENTS.md](../../REQUIREMENTS.md)
- [.planning/PROJECT.md](../../PROJECT.md)

## Code Context
- **Reusable assets**: `src/llm.py` containing `google-genai` and `openai` clients and `tenacity` retry logic.
- **Integration points**: The `_route_llm_call` function in `src/llm.py` handles the LLM generation and will need to implement the sequential provider fallback logic.
