---
phase: 03
depends_on: 02
files_modified:
  - src/llm.py
  - src/gui.py
  - src/pipeline.py
  - tests/test_llm.py
  - tests/test_pipeline.py
requirements_addressed:
  - REQ-HARD-01
  - REQ-HARD-03
---

# Phase 3: API Key Cycling & Telemetry - Plan

**Status:** Ready for execution
**Goal:** Implement robust API key cycling across 45 keys and diagnostic telemetry.

## Wave 0: Validation Scaffolding

### Task 03-00-01: Establish Test Stubs
<objective>Provision test files required for Wave 1 and Wave 2 validations.</objective>
<read_first>
- tests/test_llm.py
</read_first>
<action>
Create `tests/test_llm.py` with initial stubs and mock setups to validate key cycling, rate limits, and configuration loading. Create `tests/test_pipeline.py` with shared fixtures needed for pipeline integration tests. Ensure tests are discoverable by `pytest`.
</action>
<acceptance_criteria>
`pytest tests/` discovers and runs the new stubs successfully.
</acceptance_criteria>

## Wave 1: Key Management and Preemptive Capacity Tracking

### Task 03-01-01: API Key Loading Refactor
<objective>Support loading multiple keys.</objective>
<read_first>
- src/llm.py
- .env.example
</read_first>
<action>
Modify `GemmaClient.__init__` in `src/llm.py` to read the `GEMINI_API_KEYS` environment variable from `.env`. Split the value by commas and strip whitespace to load the 45 keys into a list, replacing the previous single `GEMINI_API_KEY` logic. Implement validation to ensure at least one key is loaded, logging a warning or error if empty. Update `.env.example` to show `GEMINI_API_KEYS=key1,key2`.
</action>
<acceptance_criteria>
`src/llm.py` initializes `GemmaClient` with a list of keys and `pytest tests/test_llm.py` passes.
</acceptance_criteria>

### Task 03-01-02: Rolling Window Trackers
<objective>Add capacity tracking per key to prevent hitting rate limits.</objective>
<read_first>
- src/llm.py
</read_first>
<action>
In `src/llm.py`, modify `GemmaClient` to maintain rolling time-based windows (e.g., `collections.deque`) for TPM (Tokens Per Minute) and RPM (Requests Per Minute) per key. Set a conservative `TPM_LIMIT` and `RPM_LIMIT` based on Google Gemini quotas. Implement a preemptive cost estimation function before each request (e.g., ~3000 tokens for image+prompt). Update `_get_client_and_key` to evaluate limits: skip a key if `current_tpm_sum + estimated_tokens >= TPM_LIMIT`, preemptively switching to the next available key. **CRITICAL:** When a key is selected, the estimated token count MUST be synchronously appended to that key's rolling window (reserved) while still holding `self.lock` *before* making the network request, preventing concurrent threads from bypassing the limit. When a key is skipped preemptively due to estimated limits, it MUST be added to `self.cooldown_keys` with a calculated release time. Update the fallback logic in `_get_client_and_key` so that if all available keys exceed limits simultaneously, it computes `sleep_time` by finding `min(self.cooldown_keys.values()) - now`. Ensure the pruning step only prunes the specific key being accessed (not all 45 keys) to prevent global lock contention. Ensure all tracker reads and modifications occur safely within `self.lock`.
</action>
<acceptance_criteria>
`GemmaClient` handles rate limits preemptively and falls back to `time.sleep` when all keys are exhausted without a `ValueError`.
</acceptance_criteria>

### Task 03-01-03: Actual Usage Reconciliation
<objective>Update tracking windows with exact usage metadata.</objective>
<read_first>
- src/llm.py
</read_first>
<action>
Update `classify_page` and `resolve_entities` in `src/llm.py` to extract `response.usage_metadata.total_token_count` from the `google.genai` response. Reconcile the exact usage by finding the previously reserved estimated token entry in the key's rolling window and updating its value to the true token count once the network call returns (under `self.lock`). Create a cleanup method to prune timestamps older than 60 seconds from the deques.
</action>
<acceptance_criteria>
`src/llm.py` successfully reads and tracks exact token usage from `usage_metadata`.
</acceptance_criteria>

## Wave 2: Diagnostic Telemetry

### Task 03-02-01: Telemetry Logger
<objective>Output detailed diagnostics to a file.</objective>
<read_first>
- src/llm.py
</read_first>
<action>
Add a dedicated file logger in `src/llm.py`. Explicitly use Python's built-in `logging` module configured with a `FileHandler` and a JSON formatter to natively ensure thread-safe writing to `telemetry.log` (do NOT use raw `open().write()`). Record each API call attempt, including `timestamp`, `key_index` (DO NOT log the raw API key), `latency_ms`, `tokens_used`, `status_code`, and `error_type` (differentiating between token limit and request limits).
</action>
<acceptance_criteria>
`telemetry.log` contains JSON lines with correctly masked key values and detailed metrics.
</acceptance_criteria>

## Wave 3: GUI Telemetry Dashboard

### Task 03-03-01: GUI Tab Refactor
<objective>Refactor the existing single-window Tkinter UI.</objective>
<read_first>
- src/gui.py
</read_first>
<action>
In `src/gui.py`, import `tkinter.ttk` and convert the main application layout to use a `Notebook` (tabs). Move the existing file selection inputs, run button, and text log into "Tab 1: Categorizer". Create "Tab 2: Telemetry" to hold the live dashboard.
</action>
<acceptance_criteria>
`src/gui.py` launches a tabbed UI containing Tab 1 and Tab 2.
</acceptance_criteria>

### Task 03-03-02: Real-time Telemetry Dashboard (Lock-Free)
<objective>Display live key stats without freezing the UI or risking concurrency micro-stutters.</objective>
<read_first>
- src/gui.py
- src/pipeline.py
</read_first>
<action>
Add a `ttk.Treeview` widget in the Telemetry tab configured as a table with columns: Key ID, Total Requests, Current RPM, Current TPM, Strikes, and Status. To avoid lock contention between the GUI's main thread and heavy background worker threads, implement a lock-free snapshot mechanism using `queue.Queue`. In `src/gui.py`, instantiate a `queue.Queue` within `FileCategorizerApp.__init__`. Modify `Pipeline.__init__` in `src/pipeline.py` to accept an optional `telemetry_queue` argument and pass it down to `GemmaClient`. Pass the queue from the GUI to `Pipeline(api_keys=api_keys, telemetry_queue=self.telemetry_queue)` inside `_execute`. Update `GemmaClient` to periodically push non-blocking state dictionaries (e.g., after each request or state change) into `self.telemetry_queue`. Do NOT acquire `GemmaClient`'s main `self.lock` from the GUI polling loop. Implement a `root.after()` polling loop in `FileCategorizerApp` that reads the latest state from the `telemetry_queue` every ~500ms and updates the Treeview rows smoothly.
</action>
<acceptance_criteria>
Tkinter `Treeview` updates dynamically via `root.after` from a lock-free `queue.Queue` without freezing the main thread.
</acceptance_criteria>

<must_haves>
  <truths>
    - D-01: Keys will be loaded via a comma-separated list in `.env` (`GEMINI_API_KEYS=key1,key2...`).
    - D-02: Track Tokens-Per-Minute (TPM) per key and switch preemptively before hitting the limit, given the large document sizes.
    - D-03: Output diagnostics to both a dedicated `telemetry.log` file and a summary view in the Tkinter GUI.
    - D-04: Track Token usage (TPM), Requests (RPM), request latency, and granular error details (differentiating between token limits and request limits).
  </truths>
</must_haves>

<threat_model>
- **ASVS Level:** 1
- **Block On:** high
- **Threats:**
  - **Exposure of Sensitive Information:** Logging of raw API keys into `telemetry.log` or the GUI dashboard. (Mitigation: Only log `key_index` or masked key identifiers. Validation: Automated tests should ensure raw keys do not appear in string output).
  - **Concurrency Race Conditions & UI Freezes:** Thread starvation or deadlocks when updating tracking structures or writing logs; UI micro-stutters from lock contention. (Mitigation: Use existing threading locks properly for internal state updates, keep lock critical sections short, and strictly enforce a lock-free mechanism like `queue.Queue` for the GUI dashboard updates to prevent cross-thread blocking).
</threat_model>
