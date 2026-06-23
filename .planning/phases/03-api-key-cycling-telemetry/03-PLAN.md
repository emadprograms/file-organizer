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

**Status:** Gaps identified — awaiting `--gaps-only` execution
**Goal:** Implement robust API key cycling across 45 keys and diagnostic telemetry.

## Investigation Findings (2026-06-23)

> Forensic analysis of `telemetry.log` (673 entries) revealed a **24% success rate**
> with systemic failures caused by code-level issues, NOT API key project conflicts.

### Telemetry Evidence

| Metric | Value |
|---|---|
| Total API calls logged | 673 |
| HTTP 200 (success) | 226 (34%) |
| HTTP 429 (rate limited) | 288 (43%) |
| HTTP 500 (server error) | 31 (5%) |
| HTTP 400 (invalid/unknown) | 128 (19%) |
| Unique API keys used | 44 |
| Effective throughput | 0.7 pages/min |
| Longest consecutive 429 streak | 78 requests |
| invalid_response errors | 66 (all with 245 tokens) |

### Root Causes Identified

1. **IP-Level Rate Limiting (PRIMARY):** All 44 keys share one IP. Google caps at ~15 RPM per IP regardless of key count. Evidence: 47 time-windows where 3+ different keys got 429'd simultaneously. Worst burst: all 44 keys hit in 80 consecutive 429s.

2. **Untracked Retry Bomb:** `classify_page` lines 306-318 fire a SECOND API call on the SAME key when model returns NONE for resident, completely bypassing `_get_client_and_key()`, the global 4s stagger, and all cooldown checks. This doubles burst rate.

3. **Concurrency Bottleneck:** 5 ThreadPool workers compete for a global lock that includes a `time.sleep(4.0)` INSIDE `with self.lock:` (line 109-112). This serializes all workers to 15 req/min maximum, regardless of key count.

4. **Invalid Responses (66 occurrences):** Model returns exactly 245-token responses that fail JSON schema parsing. Each wastes a rate-limit slot. Likely caused by blank/photo pages the model can't classify.

5. **Cascade 500s:** After burning through all keys with 429s, continued retry pressure causes server-side instability manifesting as 500 errors.

### Design Decision: IP-Level RPM Cap

**The global cap is 15 requests per minute from one IP address.** Multiple keys exist to extend the **daily quota** (1500 req/day per free key), NOT to increase throughput. The rate limiter must enforce this ceiling.

---

## Wave 0: Validation Scaffolding

### Task 03-00-01: Establish Test Stubs ✅ COMPLETE
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

### Task 03-01-01: API Key Loading Refactor ✅ COMPLETE
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

### Task 03-01-02: Rolling Window Trackers ✅ COMPLETE
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

### Task 03-01-03: Actual Usage Reconciliation ✅ COMPLETE
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

### Task 03-02-01: Telemetry Logger ✅ COMPLETE
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

### Task 03-03-01: GUI Tab Refactor ✅ COMPLETE
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

### Task 03-03-02: Real-time Telemetry Dashboard (Lock-Free) ✅ COMPLETE
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

---

## Wave 4: Gap Closure — Rate Limit Hardening (from Investigation)

> These tasks address the 5 root causes identified in the forensic investigation.
> Execute with `--gaps-only` flag.

### Task 03-04-01: Enforce Global 15 RPM IP-Level Cap
<objective>Replace the per-key-focused rate limiter with an IP-level global RPM cap of 15 requests/minute, while keeping per-key tracking for daily quota rotation.</objective>
<read_first>
- src/llm.py (lines 94-158, _get_client_and_key)
</read_first>
<gap_closure>true</gap_closure>
<action>
In `src/llm.py`, refactor `_get_client_and_key` to enforce a **global** (cross-key) RPM ceiling of 15 requests per minute:

1. Add a new class-level constant `GLOBAL_RPM_LIMIT = 15` and a new instance-level `global_rpm_tracker = deque()` in `__init__`.
2. At the TOP of the key-selection loop (before checking individual keys), prune `global_rpm_tracker` entries older than 60s, then check `len(global_rpm_tracker) >= GLOBAL_RPM_LIMIT`. If at capacity, calculate `sleep_time` from the oldest entry (`global_rpm_tracker[0] + 60 - now`) and sleep **outside** the lock.
3. When a key is selected and a request is about to be dispatched, append `time.time()` to `global_rpm_tracker` (inside the lock, alongside existing per-key tracking).
4. **Remove** the existing `time_since_last_global < 4.0` stagger check (lines 108-113) entirely — the global RPM tracker now replaces this with a more accurate, non-blocking mechanism.
5. The `time.sleep()` for global RPM must happen **outside** `with self.lock` to avoid blocking other threads from checking state.
6. Keep the existing per-key `TPM_LIMIT` and `RPM_LIMIT` tracking intact — these serve daily quota management across the 44 keys. Update `RPM_LIMIT` from 15 to a higher value (e.g., 30) since it's now the per-key-per-minute limit, not the bottleneck.

**CRITICAL:** The `time.sleep()` call on line 112 currently executes INSIDE `with self.lock:`. This must be restructured so the sleep happens OUTSIDE the lock. The pattern should be: acquire lock → check state → compute sleep_time → release lock → sleep → re-acquire lock → re-check.
</action>
<acceptance_criteria>
- `GLOBAL_RPM_LIMIT = 15` is enforced across ALL keys combined.
- No more than 15 API calls are dispatched in any rolling 60-second window regardless of key count.
- The old `4.0s` global stagger is removed.
- `time.sleep()` never executes while holding `self.lock`.
- Per-key TPM/RPM tracking still works for daily quota rotation.
</acceptance_criteria>

### Task 03-04-02: Route NONE-Resident Retry Through Rate Limiter
<objective>Eliminate the untracked retry bomb that bypasses all rate limiting when the model returns NONE for resident names.</objective>
<read_first>
- src/llm.py (lines 292-347, the retry block in classify_page)
</read_first>
<gap_closure>true</gap_closure>
<action>
In `src/llm.py`, refactor the NONE-resident retry logic in `classify_page` (lines 292-347):

1. Instead of directly calling `client.models.generate_content()` with the existing `client` variable, call `self._get_client_and_key(estimated_tokens=3000)` to obtain a fresh (or same) rate-limited client.
2. Replace `client` in the retry call with the newly acquired `retry_client`.
3. Call `self._reconcile_usage(retry_key, retry_reserve_time, retry_used_tokens)` after the retry response returns, replacing the current manual tracker update (lines 324-327).
4. Remove the manual `self.tpm_trackers[key].append(...)` and `self.rpm_trackers[key].append(...)` calls (lines 325-326) since `_get_client_and_key` now handles reservation.
5. On retry failure, call `self._report_failure(retry_key, ...)` with the correct key.
6. On retry success, call `self._report_success(retry_key)`.

**Before (current broken pattern):**
```python
retry_response = client.models.generate_content(...)  # Same client, no rate check!
with self.lock:
    self.tpm_trackers[key].append(...)  # Manual, after-the-fact
```

**After (correct pattern):**
```python
retry_client, retry_key, retry_reserve_time = self._get_client_and_key(estimated_tokens=3000)
retry_response = retry_client.models.generate_content(...)
self._reconcile_usage(retry_key, retry_reserve_time, actual_tokens)
```
</action>
<acceptance_criteria>
- The NONE-resident retry goes through `_get_client_and_key()` and respects the global 15 RPM cap.
- No direct `client.models.generate_content()` calls exist outside of `_get_client_and_key()` flow.
- Telemetry correctly logs the retry as a separate request with its own key_index and latency.
</acceptance_criteria>

### Task 03-04-03: Fix Concurrency — Sequential Pipeline With Key Rotation
<objective>Replace the 5-worker ThreadPoolExecutor with a sequential processor that uses key rotation for daily quota, since IP-level throughput is capped at 15 RPM anyway.</objective>
<read_first>
- src/pipeline.py (lines 94-110, ThreadPoolExecutor block)
- src/llm.py (lines 94-158, _get_client_and_key)
</read_first>
<gap_closure>true</gap_closure>
<action>
In `src/pipeline.py`, replace the concurrent processing with sequential execution:

1. Change `num_workers` from 5 to 1: `num_workers = 1`. This eliminates multi-thread contention while preserving the ThreadPoolExecutor structure for future re-enablement.
2. Remove the `cancel_event` and `cancel_event.is_set()` checks — with a single worker, cancellation can be handled via exception propagation directly.
3. Keep the `cache_lock` for progressive caching (still needed for crash safety).
4. Update the print statement to reflect: `Processing {n} pages sequentially (15 RPM global cap)...`

In `src/llm.py`, remove the now-unnecessary `delay_between_pages` sleep on lines 350 and 454 (`time.sleep(self.delay_between_pages)`). The global RPM tracker from Task 03-04-01 now controls pacing — an additional sleep creates unnecessary dead time.

**Rationale:** With a 15 RPM IP-level cap, 5 workers fighting over one lock that releases every 4 seconds produces exactly the same throughput as 1 worker. The concurrency adds complexity (lock contention, thundering herd on cooldowns) with zero throughput benefit. The multiple keys still rotate for daily quota spreading.
</action>
<acceptance_criteria>
- Pipeline processes pages sequentially with `num_workers = 1`.
- `delay_between_pages` sleep is removed from `classify_page` and `resolve_entities`.
- Throughput is still ~15 pages/min (unchanged from the locked concurrent model, but now without contention overhead).
- The `_get_client_and_key` round-robin still rotates across all 44 keys for daily quota distribution.
</acceptance_criteria>

### Task 03-04-04: Handle Invalid Responses Gracefully
<objective>Stop wasting rate-limit capacity on pages that consistently produce unparseable 245-token responses.</objective>
<read_first>
- src/llm.py (lines 282-290, response parsing in classify_page)
- src/schemas.py (PageClassification schema)
</read_first>
<gap_closure>true</gap_closure>
<action>
In `src/llm.py`, improve the invalid response handling in `classify_page`:

1. When `response.parsed is None` AND `json.loads(response.text)` fails (the `InvalidResponseError` path on lines 288-290), log the **actual raw response text** to the telemetry logger with error_type `"model_refusal"` and include the first 200 chars of `response.text` in the log entry (new field: `"raw_preview"`). **CRITICAL:** Accessing `response.text` on a model refusal or safety-blocked response can raise a `ValueError`. Wrap the `response.text` access in a `try/except ValueError` or check `response.candidates[0].finish_reason` before accessing it to prevent thread crashes.
2. Add a `max_invalid_retries = 2` counter specifically for `InvalidResponseError`. If the same page produces 2 consecutive invalid responses, **stop retrying that page** and return a fallback `PageClassification` with `category=Category.OTHER_LETTERS`, `residents=["NONE"]`, `date="NONE"`, and `house_number` extracted from the first successful response or "UNKNOWN". Log this as a `"fallback_classification"` event.
3. In the telemetry log entry for invalid responses, add the `tokens_used` from the response (currently logged as 0 even though the API returned 245 tokens) — use the actual `usage_metadata.total_token_count` value.

**Rationale:** 66 out of 673 calls (10%) are wasted on invalid responses. These are likely blank pages or photographs that the model cannot classify. Instead of burning 7+ retry attempts per page (each consuming a rate-limit slot), cap at 2 and move on with a safe fallback.
</action>
<acceptance_criteria>
- Invalid responses log `raw_preview` of the model's actual output for debugging.
- After 2 invalid responses on the same page, a fallback `PageClassification` is returned.
- No more than 2 rate-limit slots are consumed per unparseable page.
- `tokens_used` is correctly reported for invalid responses (not 0).
</acceptance_criteria>

### Task 03-04-05: Add Exponential Backoff With Jitter on 429s
<objective>Replace the flat cooldown escalation with exponential backoff + jitter to prevent 429 cascades from snowballing into 500s.</objective>
<read_first>
- src/llm.py (lines 168-188, _report_failure method)
</read_first>
<gap_closure>true</gap_closure>
<action>
In `src/llm.py`, refactor `_report_failure`:

1. Replace the flat `cooldown_periods = {1: 15, 2: 30, 3: 60, 4: 120}` dictionary with exponential backoff: `penalty = min(15 * (2 ** (strikes - 1)), 300)` — this gives 15s, 30s, 60s, 120s, 240s, capped at 300s.
2. Add **jitter** to prevent thundering herd: `penalty = penalty * (0.5 + random.random())` (import `random` at the top of the file). This spreads retries across a time window instead of having all keys retry at exactly the same moment.
3. On 429 errors, set `global_cooldown_until` to `now + penalty` (the SAME penalty as the key-level cooldown), not a flat 15s. This prevents other threads from immediately burning more keys during the backoff window.
4. Remove the separate `global_cooldown_until = max(self.global_cooldown_until, now + 5.0)` for 500 errors (line 185). Instead, use the same exponential formula. Server errors need MORE rest, not less.
5. Add a `max_strikes` constant of 10. If any key reaches 10 strikes, log a CRITICAL telemetry event and put the key in permanent cooldown for the remainder of the session (`cooldown_keys[key] = float('inf')`). **CRITICAL:** Update `_get_client_and_key` to handle the case where all keys are exhausted and `min(self.cooldown_keys.values()) == float('inf')`. If the min sleep time is `inf`, raise a `RuntimeError` ("All API keys exhausted permanently") instead of sleeping indefinitely, preventing a permanent application freeze.
</action>
<acceptance_criteria>
- Backoff is exponential: 15s → 30s → 60s → 120s → 240s → 300s (capped).
- Jitter of ±50% is applied to all cooldown periods.
- `global_cooldown_until` uses the full penalty duration on 429s.
- Keys with 10+ strikes are permanently retired for the session.
- No more cascade patterns of 78+ consecutive 429s in the telemetry log.
</acceptance_criteria>

---

<must_haves>
  <truths>
    - D-01: Keys will be loaded via a comma-separated list in `.env` (`GEMINI_API_KEYS=key1,key2...`).
    - D-02: Track Tokens-Per-Minute (TPM) per key and switch preemptively before hitting the limit, given the large document sizes.
    - D-03: Output diagnostics to both a dedicated `telemetry.log` file and a summary view in the Tkinter GUI.
    - D-04: Track Token usage (TPM), Requests (RPM), request latency, and granular error details (differentiating between token limits and request limits).
    - D-05: **Global IP-level RPM cap is 15 requests/minute.** Multiple keys exist for daily quota extension ONLY, not throughput multiplication.
    - D-06: All API calls (including retries) MUST go through the rate limiter. No direct `client.models.generate_content()` calls outside the rate-limiting flow.
  </truths>
</must_haves>

<threat_model>
- **ASVS Level:** 1
- **Block On:** high
- **Threats:**
  - **Exposure of Sensitive Information:** Logging of raw API keys into `telemetry.log` or the GUI dashboard. (Mitigation: Only log `key_index` or masked key identifiers. Validation: Automated tests should ensure raw keys do not appear in string output).
  - **Concurrency Race Conditions & UI Freezes:** Thread starvation or deadlocks when updating tracking structures or writing logs; UI micro-stutters from lock contention. (Mitigation: Use existing threading locks properly for internal state updates, keep lock critical sections short, and strictly enforce a lock-free mechanism like `queue.Queue` for the GUI dashboard updates to prevent cross-thread blocking).
  - **Rate Limit Cascade (NEW):** Untracked retries and concurrent workers bypassing the rate limiter cause cascading 429s that snowball into 500s. (Mitigation: All API calls routed through `_get_client_and_key()`. Global RPM cap of 15. Exponential backoff with jitter on failures).
</threat_model>

