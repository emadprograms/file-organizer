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

### Task 1: Configuration & Models
<read_first>
- src/config.py
</read_first>
<action>
Modify `src/config.py` to add constants for the fallback models:
1. `OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "gemma-4-26b-a4b-it")`
2. `GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen3.6-27b")`
</action>
<acceptance_criteria>
`src/config.py` exposes `OPENROUTER_MODEL` and `GROQ_MODEL`.
</acceptance_criteria>

### Task 2: Add OpenAI Clients to `GemmaClient`
<read_first>
- src/llm.py
</read_first>
<action>
Modify `GemmaClient.__init__` in `src/llm.py`:
1. Add `import openai` at the top of the file.
2. In `GemmaClient.__init__`, fetch `OPENROUTER_API_KEY` and `GROQ_API_KEY` from `os.getenv()`.
3. Initialize `self.openrouter_client = openai.Client(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")`.
4. Initialize `self.groq_client = openai.Client(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")`.
</action>
<acceptance_criteria>
`src/llm.py` contains `import openai` and initializes `self.openrouter_client` and `self.groq_client`.
</acceptance_criteria>

### Task 3: Implement Fallback Chain with SDK Translation in `_route_llm_call`
<read_first>
- src/llm.py
- .planning/phases/03-cloud-fallback/03-CONTEXT.md
- src/config.py
</read_first>
<action>
Rewrite the error handling and execution flow in `_route_llm_call` in `src/llm.py`:
1. Implement a provider sequence: Try Gemini first. 
2. **SDK Translation**: If falling back to OpenRouter or Groq, you must translate the Google GenAI prompt into the OpenAI format: `messages=[{"role": "user", "content": prompt_content}]`.
3. **5xx/Timeouts**: If a 5xx or timeout occurs on Gemini, immediately try OpenRouter (using `config.OPENROUTER_MODEL`). If OpenRouter throws a 5xx/timeout, fall back to Groq (`config.GROQ_MODEL`).
4. **Auth Errors**: If an authentication error (401/403) occurs on any provider, do *not* fail over or retry. Raise the error immediately to fail fast.
5. **Rate Limits (429)**: If any provider throws a 429 error, sleep for 65 seconds and retry the *current* provider. Add a maximum retry limit of 3 to prevent infinite loops.
6. For OpenRouter and Groq, make calls using `chat.completions.create` and extract the result from `response.choices[0].message.content`. Pass `response_format={"type": "json_object"}`.
7. Print `[Cloud Fallback] Failed over to OpenRouter` and `[Cloud Fallback] Failed over to Groq` to stdout when failover occurs.
8. The function must return the parsed Pydantic object without adding provider metadata.
</action>
<acceptance_criteria>
`_route_llm_call` routes 5xx/timeout errors sequentially, translates inputs to the `openai` SDK format for OpenRouter/Groq, fails fast on auth errors, and caps 429 retries at 3.
</acceptance_criteria>
