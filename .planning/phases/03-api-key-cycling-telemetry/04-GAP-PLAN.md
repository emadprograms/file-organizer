# Phase 03: API Key Cycling & Telemetry - Gap Closure

## Wave 1: Gap Closure

### Task 03-GAP-01: Fix Invalid Response Fallback Bug - [x] Completed
<objective>Ensure the system gracefully falls back to `OTHER_LETTERS` after 2 invalid LLM responses instead of crashing after 7 max retries.</objective>
<read_first>
- src/llm.py (lines 445-460)
- src/pipeline.py (lines 100-110)
</read_first>
<gap_closure>true</gap_closure>
<action>
In `src/llm.py`, modify the exception block in `classify_page` (around lines 448-450):
1. Immediately after incrementing `invalid_retries += 1`, add a check: `if invalid_retries >= 2: raise InvalidResponseError(raw_preview)`
2. This ensures that after 2 failures, the error bubbles up to `pipeline.py` which will catch it and properly return the fallback `Category.OTHER_LETTERS` classification.
</action>
<acceptance_criteria>
- The system correctly breaks the retry loop after 2 invalid responses.
- `pipeline.py` catches the `InvalidResponseError` and falls back correctly.
</acceptance_criteria>

### Task 03-GAP-02: Build Automated Tests for Rate Limiting & Failures - [x] Completed
<objective>Create a dedicated test file to automatically verify invalid LLM response handling and global IP freezing.</objective>
<read_first>
- src/llm.py
- src/pipeline.py
</read_first>
<gap_closure>true</gap_closure>
<action>
1. Create a `tests/` directory if it does not exist.
2. Create `tests/test_llm_resilience.py`.
3. Use `unittest.mock` to simulate `InvalidResponseError` and verify that `pipeline.process_single_page` handles it by returning `OTHER_LETTERS`.
4. Create a test that simulates a `429` with `Resource Exhausted` and verify `global_cooldown_until` is updated properly.
5. Create a test that simulates `InvalidResponseError` inside `llm.py` and verify it raises the exception after exactly 2 retries.
</action>
<acceptance_criteria>
- The test suite covers invalid LLM responses.
- The test suite covers 429 global IP freezing.
- Tests can be run locally using `python -m unittest tests/test_llm_resilience.py`.
</acceptance_criteria>

### Task 03-GAP-03: Strip Markdown from LLM JSON Responses - [x] Completed
<objective>Ensure `json.loads()` does not fail when the LLM wraps valid JSON inside ` ```json ... ``` ` markdown blocks.</objective>
<read_first>
- src/llm.py
</read_first>
<gap_closure>true</gap_closure>
<action>
In `src/llm.py`, update the JSON parsing logic in both `classify_page` and `resolve_entities`:
1. Before calling `json.loads(response.text)`, check if `response.text` contains markdown code blocks.
2. Strip ` ```json ` and ` ``` ` from the string, or use a regex to extract the JSON block.
3. This will rescue valid responses (often ~245 tokens) that are currently being discarded as `InvalidResponseError` simply because of markdown formatting.
</action>
<acceptance_criteria>
- `json.loads()` successfully parses JSON wrapped in markdown.
- Fewer `InvalidResponseError` events occur in the telemetry logs.
</acceptance_criteria>

### Task 03-GAP-04: Ultra-Safe Rate Limiting & Persistence - [x] Completed
<objective>Persist `global_rpm_tracker` to a file so the app remembers requests across restarts, and drop the proactive limit to 10 RPM to guarantee we never hit Google's 15 RPM wall.</objective>
<read_first>
- src/llm.py
</read_first>
<gap_closure>true</gap_closure>
<action>
In `src/llm.py`, modify `GemmaClient` to be ultra-conservative:
1. Change `GLOBAL_RPM_LIMIT = 10` (down from 12). This gives a massive 33% safety buffer because Google's internal sliding window calculation clearly differs from ours if we process pages slowly over 60s.
2. Create a hidden state file path (e.g. `.rate_limit_state.json` in the project root).
3. On `__init__`, try to load `global_rpm_tracker` (as a list of floats) and `global_cooldown_until` from this file.
4. Every time `global_rpm_tracker` or `global_cooldown_until` is updated, save the current state to the JSON file.
5. This ensures the app ALWAYS proactively sleeps before reaching 15, even if stopped and restarted.
</action>
<acceptance_criteria>
- `GLOBAL_RPM_LIMIT` is strictly 10.
- The app remembers API requests across process restarts.
- The app proactively sleeps before hitting a 429 error.
</acceptance_criteria>
