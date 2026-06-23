---
phase: 03
reviewers: [codex]
reviewed_at: 2026-06-23T11:25:00Z
plans_reviewed: [03-PLAN.md]
---

# Cross-AI Plan Review — Phase 03

## Codex Review

### Summary
The plan is highly detailed and addresses the API key cycling and telemetry goals comprehensively. The use of rolling time-based windows and a lock-free queue for the Tkinter UI are excellent architectural choices. However, there are significant concurrency risks regarding how estimated capacity is reserved before API calls are made, and potential blocking issues under the global lock during heavy queue pruning.

### Strengths
- Uses `queue.Queue` to completely isolate the Tkinter UI thread from the background LLM workers, avoiding GUI freezes.
- Preemptive token estimation is a strong approach to avoiding 429s entirely.
- Clear separation of diagnostic telemetry (JSONL file) and user-facing GUI telemetry.

### Concerns
- **HIGH: Concurrent Capacity Reservation Race Condition**
  - **Issue:** Task 03-01-02/03-01-03 describes checking `current_tpm_sum + estimated_tokens >= TPM_LIMIT` and later correcting it with actual tokens. However, if 5 worker threads check the limit simultaneously *before* any have completed, they will all see the same `current_tpm_sum` and may all fire requests, hitting the 429 rate limit. 
  - **Impact:** Thundering herd effect bypassing rate limits.
- **MEDIUM: Global Lock Contention during Pruning**
  - **Issue:** Pruning old entries from the `collections.deque` under the main `self.lock` for 45 keys could introduce latency spikes that block other threads from simply getting a key.
  - **Impact:** Micro-stutters in pipeline performance.
- **LOW: Raw File Thread-Safety**
  - **Issue:** Task 03-02-01 mentions "thread-safe logging" but doesn't specify using Python's `logging` module. Using raw `open().write()` concurrently will corrupt the JSONL.

### Suggestions
- **For the Capacity Race Condition:** Update Task 03-01-02 to explicitly state that the estimated token count must be *appended* to the key's rolling window (i.e. "reserved") while holding `self.lock` *before* releasing the lock and making the network request. Task 03-01-03 should then reconcile by finding that estimated entry and updating its value to the true token count once the network call returns.
- **For Lock Contention:** Ensure the pruning step only prunes the specific key being accessed rather than looping through all 45 keys every time, keeping the `self.lock` critical section as short as possible.
- **For Telemetry Logging:** Explicitly use Python's built-in `logging` module configured with a `FileHandler` and JSON formatter, which natively provides thread-safety.

### Risk Assessment
- **MEDIUM** - The architecture is sound, but missing the "capacity reservation" detail in the concurrent estimation step will almost certainly lead to the exact 429 errors the phase is trying to prevent.

---

## Consensus Summary

The plan strongly covers the requirements but has critical gaps in concurrency logic regarding token capacity reservation across multiple threads.

### Agreed Strengths
- Excellent use of lock-free queue for the GUI.
- Preemptive capacity checking rather than reactive backoff.

### Agreed Concerns
- **HIGH:** Concurrent capacity reservation race condition. If estimated tokens are not synchronously reserved under the lock before the network call, concurrent threads will bypass the limit.

### Divergent Views
- None (Single reviewer evaluation).
