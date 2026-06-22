## ROOT CAUSE FOUND

**Debug Session:** .planning/debug/thinking-budget.md

**Root Cause:** The `gemma-4-31b-it` model does not support the `thinking_config` or `thinking_budget` parameters via the Google GenAI API, causing a `400 INVALID_ARGUMENT` crash on startup.

**Evidence Summary:**
- The UAT stack trace showed: `google.genai.errors.ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Thinking budget is not supported for this model.', 'status': 'INVALID_ARGUMENT'}}`
- Line 98 of `src/llm.py` explicitly configures `thinking_config=types.ThinkingConfig(thinking_budget=0)` in the `generate_content` call.

**Files Involved:**
- `src/llm.py`: Lines 95-100 pass a `thinking_config` parameter to a model that does not support it.

**Suggested Fix Direction:** Remove `thinking_config=types.ThinkingConfig(thinking_budget=0),` from the `GenerateContentConfig` in `src/llm.py`.
