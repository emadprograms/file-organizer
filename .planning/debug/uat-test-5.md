# UAT Test 5: Root Cause Analysis

## Issue
**Reported:** "fail. The system crashes instead of failing over."
**Expected:** "If a provider returns a 401 or 403 authorization error (e.g., due to an invalid key), the system immediately fails over to the next provider without attempting to retry."

## Root Cause
The `_route_llm_call` function was correctly failing over on authentication errors across Gemini, OpenRouter, and Groq. However, if *all* providers were tested with invalid keys (which is the case when simulating complete authentication failover), the loop exhausts all providers and correctly raises `RuntimeError("LLM routing failed across all providers")`.

While most pipeline stages (like `classify_page_direct` and `detect_date_outliers`) had `try/except` blocks that handled this gracefully, the `check_bulk_semantic_grouping` function did not. When the final `RuntimeError` bubbled up during semantic grouping, it explicitly re-raised it:
```python
        except Exception as e:
            print(f"WARNING: Direct Cloud bulk grouping failed: {e}")
            self.activate_cooldown()
            raise  # <-- Caused the crash
```
This unhandled exception bubbled all the way up to `main.py`, causing the application to abruptly crash instead of failing gracefully.

## Fix Implemented
1. Modified `check_bulk_semantic_grouping` in `src/llm.py` to catch the exception and return a default fallback grouping (where each page is its own standalone group) instead of raising the exception.
2. Verified that the auth error checks for 400 (Gemini invalid key) and "api key not valid" are preserved so fail-fast continues to work without wasting time on retries.

The system will no longer crash and will gracefully complete the pipeline even if all LLM providers fail.
