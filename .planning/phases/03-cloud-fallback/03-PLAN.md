---
wave: 1
depends_on: []
files_modified:
  - src/llm.py
autonomous: true
---

# Phase 03 Plan: Cloud Fallback

## Objective
Implement Gemini -> OpenRouter -> Groq chain for cloud fallback.

## must_haves
- requirements: CLOUD-01, CLOUD-02, CLOUD-03
- truths:
  - `src/llm.py` imports `openai` and initializes `openrouter_client` and `groq_client`.
  - `_route_llm_call` implements the sequential fallback chain: Gemini -> OpenRouter -> Groq.
  - OpenRouter uses the `gemma-4-26b-a4b-it` model.
  - Groq uses the `qwen3.6-27b` model.
  - On 429 errors or token limits, the system pauses for 65s and retries the current provider.
  - On 500/503 errors, the system falls back immediately to the next provider in the chain.
  - On fallback, the system prints `[Cloud Fallback] Failed over to <Provider>` to stdout.
- prohibitions:
  - statement: Do not pollute the JSON cache schema with provider metadata.
    status: resolved
    verification: Returning values from `_route_llm_call` must exactly match the `response_schema` without adding extra fields for the provider used.

## Artifacts this phase produces
- `src/llm.py:GemmaClient.openrouter_client` (field)
- `src/llm.py:GemmaClient.groq_client` (field)

## Tasks

### Task 1: Add OpenAI Clients to `GemmaClient`
<read_first>
- src/llm.py
</read_first>
<action>
Modify `GemmaClient.__init__` in `src/llm.py`:
1. Add `import openai` at the top of the file.
2. In `GemmaClient.__init__`, fetch `OPENROUTER_API_KEY` and `GROQ_API_KEY` from `os.getenv()`.
3. Initialize `self.openrouter_client = openai.Client(api_key=..., base_url="https://openrouter.ai/api/v1")`.
4. Initialize `self.groq_client = openai.Client(api_key=..., base_url="https://api.groq.com/openai/v1")`.
</action>
<acceptance_criteria>
`src/llm.py` contains `import openai` and initializes `self.openrouter_client` and `self.groq_client`.
</acceptance_criteria>

### Task 2: Implement Fallback Chain in `_route_llm_call`
<read_first>
- src/llm.py
- .planning/phases/03-cloud-fallback/03-CONTEXT.md
</read_first>
<action>
Rewrite the error handling and execution flow in `_route_llm_call` in `src/llm.py`:
1. Implement a provider sequence: Try Gemini first. If a 5xx/timeout exception occurs, catch it and immediately try OpenRouter (`model="gemma-4-26b-a4b-it"`). If OpenRouter throws a 5xx/timeout exception, fall back to Groq (`model="qwen3.6-27b"`).
2. For OpenRouter and Groq, make calls using their respective `chat.completions.create` functions, passing `response_format={"type": "json_object"}`. 
3. If any provider throws a 429 error (or rate limit / quota error), sleep for 65 seconds and retry the *current* provider (do not fail over).
4. If a JSON parsing error occurs, treat it as an invalid response and retry on the *current* provider.
5. Print `[Cloud Fallback] Failed over to OpenRouter` and `[Cloud Fallback] Failed over to Groq` to stdout when failover occurs.
6. The function must return the parsed Pydantic object as it currently does, without adding provider metadata to it.
</action>
<acceptance_criteria>
`_route_llm_call` successfully routes failed Gemini requests to OpenRouter, and failed OpenRouter requests to Groq, and continues to respect the 65s pause on 429 errors without skipping to the next provider.
</acceptance_criteria>
