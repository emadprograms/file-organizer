# Phase 03 Patterns: Cloud Fallback

## 1. `src/llm.py`

**Role**: Orchestrates all LLM API calls, managing retries, fallback logic, and routing generation requests to multiple providers.
**Data Flow**: Receives standard text/image prompts and a Pydantic schema -> Attempts Google GenAI -> Catches 500/503 errors -> Falls back to OpenRouter -> Catches 500/503 errors -> Falls back to Groq -> Returns the parsed Pydantic object.

**Closest Existing Analog**:
The `_route_llm_call` function inside the `GemmaClient` class in `src/llm.py`.

**Concrete Code Excerpt**:
```python
    def _route_llm_call(self, model: str, contents: list, response_schema: type, log_prefix: str = "Retry", max_attempts: Optional[int] = None) -> Any:
        attempts = 0
        if max_attempts is None:
            max_attempts = 7
        invalid_retries = 0
        
        while attempts < max_attempts:
            attempts += 1
            start_time = time.time()
            
            try:
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                future = executor.submit(
                    self.client.models.generate_content,
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0
                    )
                )
# ... [retry logic on exceptions for 429 and 5xx] ...
```

**Planned Modifications**:
- Introduce the `openai` Python package to interface with OpenRouter and Groq.
- Refactor the error handling inside `_route_llm_call` or create an orchestrator class:
  - **429 Errors**: Continue to pause for 65s and retry the current provider (do not fail over).
  - **500/503 Errors**: Fail fast and fallback immediately to the next provider instead of retrying.
- **Provider Chain**: 
  - Primary: Google GenAI (Gemini models)
  - Secondary: OpenRouter (`gemma-4-26b-a4b-it`)
  - Tertiary: Groq (`qwen3.6-27b`)
- Output explicit `stdout` logs on fallback (e.g., `print("[Cloud Fallback] Failed over to OpenRouter")`).
- Keep the returned structures clean and don't pollute the JSON responses or cache files with provider metadata.
