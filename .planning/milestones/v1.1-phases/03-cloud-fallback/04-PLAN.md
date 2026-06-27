---
wave: 2
depends_on: []
files_modified:
  - src/config.py
  - src/llm.py
autonomous: true
---

# Phase 03 Plan: Cloud Fallback UAT Gaps

## Objective
Address UAT gaps: make OpenRouter and Groq optional, and ensure 401/403 authorization errors immediately fail over to the next provider instead of crashing or retrying.

## must_haves
- requirements: CLOUD-01, CLOUD-02, CLOUD-03
- truths:
  - `src/config.py` does not require `OPENROUTER_API_KEY` and `GROQ_API_KEY` to start the application.
  - `_route_llm_call` dynamically skips OpenRouter if `self.openrouter_client` is None.
  - `_route_llm_call` dynamically skips Groq if `self.groq_client` is None.
  - If a provider returns a 401 or 403 error, `_route_llm_call` immediately fails over to the next provider without attempting to retry.
- prohibitions:
  - statement: Do not crash or raise an exception on 401/403 errors if there are fallback providers remaining.
    status: resolved
    verification: `_route_llm_call` must catch auth errors and move to the next provider in the `providers` list.

## Artifacts this phase produces
- (None - modifying existing files)

## Tasks

### Task 1: Make Fallback Providers Optional in Config
<read_first>
- src/config.py
</read_first>
<action>
Modify `load_config` in `src/config.py`:
1. Remove `OPENROUTER_API_KEY` and `GROQ_API_KEY` from the `missing_keys` check.
2. Only `GEMINI_API_KEY` should be considered a required API key that causes a `sys.exit(1)`.
</action>
<acceptance_criteria>
`src/config.py` can be loaded successfully when `OPENROUTER_API_KEY` and `GROQ_API_KEY` are not set in the environment.
</acceptance_criteria>

### Task 2: Skip Unconfigured Providers and Fail Over on Auth Errors
<read_first>
- src/llm.py
- src/config.py
</read_first>
<action>
Modify `_route_llm_call` in `src/llm.py`:
1. Filter the `providers` list before the `while` loop so that `"openrouter"` is only included if `self.openrouter_client` is not `None`, and `"groq"` is only included if `self.groq_client` is not `None`.
2. Change the error handling for `is_auth` (401/403 errors). Instead of raising `LLMFailureError` immediately, it must immediately advance to the next provider (`current_provider_idx += 1`), print `[Cloud Fallback] Failed over to {next_name}`, and `continue`.
3. If it was the last provider in the sequence, it should naturally fall through the `while` loop and raise the `RuntimeError("LLM routing failed across all providers")` at the end of the function.
</action>
<acceptance_criteria>
`_route_llm_call` skips OpenRouter/Groq if their clients are `None`. It catches 401/403 errors and fails over to the next provider without retrying.
</acceptance_criteria>
