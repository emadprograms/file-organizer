# Phase 3: API Key Cycling & Telemetry - Research

## 1. What do I need to know to PLAN this phase well?

To successfully plan Phase 3, we need to transition our system from a reactive rate-limiting model to a proactive, telemetry-driven one.

### Current State & Limitations
- **`GemmaClient` (`src/llm.py`)**: Currently uses a reactive round-robin approach. It switches keys *only* after encountering a failure (e.g., 429 Rate Limit or 5xx) and then triggers a global throttle lock. This guarantees we hit rate limits before cycling, which we want to avoid.
- **Concurrency (`src/pipeline.py`)**: Processes up to 5 pages concurrently using `ThreadPoolExecutor`. Simultaneous rate-limit hits across threads currently cause a "thundering herd" effect that aggressively blocks the pipeline.
- **GUI Limitations (`src/gui.py`)**: It is a single-window interface with a single `ScrolledText` log. There is no dedicated UI panel to show real-time telemetry or key capacity limits.

### Key Cycling & Capacity Tracking Plan
To preemptively switch keys (Requirement HARD-01, D-02), we need:
- **Rolling Window Trackers**: Track Tokens-Per-Minute (TPM) and Requests-Per-Minute (RPM) per key using time-based sliding windows (e.g., `collections.deque` storing `(timestamp, amount)` within a 60-second window).
- **Preemptive Estimation**: Before an API call is made, estimate its cost (e.g., 1 image + prompt ≈ 3,000 tokens) to ensure the selected key's `current_tpm_sum + estimated_tokens` is strictly less than the `TPM_LIMIT`. If the limit would be exceeded, the key should be skipped *before* issuing the request.
- **Actual Usage Reconciliation**: After a successful API response, the system should read the exact token consumption (via the `google.genai` response's `usage_metadata.total_token_count`) and update the key's rolling window to maintain accuracy.
- **Thread Safety**: All reads, limit checks, and updates to the rolling windows must happen safely inside `GemmaClient`'s existing `self.lock`.

### Telemetry & Diagnostics Plan
To fulfill diagnostic requirements (Requirement HARD-03, D-03, D-04):
- **Structured Logging (`telemetry.log`)**: Implement a dedicated file logger (JSONL format is recommended) that logs each request's `timestamp`, `key_index`, `latency_ms`, `tokens_used`, `status_code`, and `error_type`. This allows clear offline diagnosis of token bucket exhaustion vs request limits.
- **GUI Refactoring (`src/gui.py`)**:
  - Convert the main application layout to use `tkinter.ttk.Notebook` (tabs).
  - **Tab 1 (Categorizer)**: The existing file selection and text logs UI.
  - **Tab 2 (Telemetry)**: A live dashboard using `ttk.Treeview` configured as a table with columns: `Key ID`, `Total Requests`, `Current RPM`, `Current TPM`, `Strikes`, and `Status`. 
  - **Polling System**: Implement a `root.after()` polling loop in the Tkinter main thread to periodically fetch a snapshot of the telemetry data from `GemmaClient` and update the `Treeview` without blocking the main event thread.

## Validation Architecture

To ensure the new capabilities meet the Nyquist Validation requirement and the phase success criteria:

1. **Unit Testing (Preemptive Logic)**
   - Mock the API client to return specific token usage metadata without making real network requests.
   - Assert that `GemmaClient` switches to the next available key exactly when the preemptive threshold (TPM or RPM) is breached by the estimation logic, *before* any mock `429` error is received.

2. **Integration & Telemetry Audit**
   - Run a 20-page dummy PDF workload using an artificially lowered TPM limit configuration (e.g., max 5,000 TPM limit).
   - Audit the generated `telemetry.log` to confirm that every request accurately recorded its latency, token count, and key ID, and that the JSONL logs are properly formatted.

3. **Concurrency Simulation**
   - Execute the pipeline with a high thread count (e.g., 10 concurrent workers) but limited API keys (e.g., 2 simulated keys).
   - Verify that the threading locks around the rolling window trackers successfully prevent race conditions and accurately reflect RPM without skipping or double-counting capacity.

4. **GUI Responsiveness Validation**
   - While processing a large document, observe the Tkinter application. The Telemetry tab's `Treeview` must update its stats in real-time and the application window must not freeze.
