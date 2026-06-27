# Plan Summary: 03

## What was done
- Added `OPENROUTER_MODEL` and `GROQ_MODEL` constants to `src/config.py`.
- Added `import openai` and initialized `self.openrouter_client` and `self.groq_client` inside `GemmaClient.__init__` in `src/llm.py`.
- Implemented a cloud fallback chain in `_route_llm_call` in `src/llm.py`:
  - Starts with Gemini, falls back sequentially to OpenRouter, then Groq.
  - Translates Google GenAI SDK `contents` to OpenAI `messages` format upon failover.
  - Handles 429 errors by sleeping 65 seconds and retrying the current provider (max 3 retries per provider).
  - Handles 5xx and timeout errors by immediately failing over to the next provider.
  - Fails fast on 401/403 auth errors.
  - Returns raw parsed JSON/Pydantic objects without metadata pollution.

## Artifacts produced
- `src/config.py`: `OPENROUTER_MODEL`, `GROQ_MODEL`
- `src/llm.py:GemmaClient.openrouter_client` (field)
- `src/llm.py:GemmaClient.groq_client` (field)
