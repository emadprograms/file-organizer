# Phase 03: Cloud Fallback Research

## Objective
Research the requirements and current state to plan the implementation of the `Gemini -> OpenRouter -> Groq` fallback chain.

## Current State Analysis (`src/llm.py`)
- **Clients**: Currently, `src/llm.py` only implements a `GemmaClient` using the `google-genai` SDK. The `openai` client (needed for OpenRouter and Groq) is not yet imported or implemented.
- **Retry Logic**: There is no `tenacity` logic present despite the context mentioning it as a reusable asset. The code uses a custom `while attempts < max_attempts` loop in `_route_llm_call`.
- **Current Model References**: The code currently hardcodes `model='gemma-4-26b-a4b-it'` for `classify_page_direct` and `check_bulk_semantic_grouping` using the `google-genai` client, which may be incorrect for Google GenAI but should be routed to OpenRouter as per the context.

## Requirements for Planning

To plan this phase well, we must address the following:

### 1. API Clients & Configuration
- We need to introduce the `openai` Python package to interface with OpenRouter and Groq since both provide OpenAI-compatible APIs.
- We must ensure `OPENROUTER_API_KEY` and `GROQ_API_KEY` are retrieved from the environment or `src/config.py`.

### 2. Provider Chain Logic
- **Primary**: Google GenAI (Gemini models).
- **Secondary**: OpenRouter (`gemma-4-26b-a4b-it`).
- **Tertiary**: Groq (`qwen3.6-27b`).

### 3. Fallback vs. Retry Conditions
The error handling inside `_route_llm_call` needs a significant refactor to accommodate provider switching:
- **429 Errors (Rate Limits)**: Wait 65s and **retry** the current provider. Do not fail over.
- **500/503 Errors (Service Outages)**: Fail fast and **fallback immediately** to the next provider in the chain.
- **Invalid Response (JSON Parsing)**: Should likely retry on the same provider or fail over if max retries are reached.
- Need to map both `google.genai.errors` and `openai.APIError` correctly.

### 4. Code Structure Refactor
- Either refactor `GemmaClient` into a generic `LLMClient` that manages all three providers, or create separate client classes wrapped by an orchestrator in `src/llm.py`.
- The `_route_llm_call` function must encapsulate the chain logic: `try Gemini -> except 5xx -> try OpenRouter -> except 5xx -> try Groq`.

### 5. Logging
- Implement clear `stdout` logging on failovers (e.g., `print("[Cloud Fallback] Failed over to OpenRouter")`).
- Keep the return schemas clean; do not pollute the JSON responses or cache files with provider metadata.

## Conclusion
The plan will require updating `src/llm.py` to include the `openai` client, restructuring the retry loop to implement the sequential fallback on 500/503 errors while maintaining the 65s pause on 429s, and configuring the correct models per provider.
