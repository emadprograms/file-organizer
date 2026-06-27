# UAT Test 4 Debug

## Issue
User requested enhancement: Make OpenRouter and Groq optional. Fallback logic should dynamically skip providers that do not have an API key configured, instead of crashing or wasting time retrying.

## Root Cause
Prior to the fix in commit `c0561b97`:
1. `src/config.py`'s `load_config` strictly required `OPENROUTER_API_KEY` and `GROQ_API_KEY` to be set. If they were missing, it added them to `missing_keys` and exited the application with a `sys.exit(1)` fatal error.
2. `src/llm.py`'s `GemmaClient._route_llm_call` hardcoded the list `providers = ["gemini", "openrouter", "groq"]`. This meant the application always attempted to route to these providers regardless of whether their API keys were configured, which would lead to crashes or wasted retries.

## Resolution
This issue was recently resolved by:
1. Modifying `src/config.py` to only append missing optional keys to `optional_missing` and log a warning instead of a fatal error.
2. Modifying `src/llm.py` to dynamically construct the `providers` list (e.g., `providers = ["gemini"]`, then appending `openrouter` and `groq` only if `self.openrouter_client` and `self.groq_client` are successfully instantiated).
