---
status: "issues_found"
files_reviewed: 2
critical: 2
warning: 3
info: 3
total: 8
---

### CR-1: NameError on Fallback Classification
In `llm.py`, when a classification fails due to invalid JSON parsing (`invalid_retries >= 2`), the code attempts to return a fallback response using `category=Category.OTHER_LETTERS`. However, the `Category` enum is never imported in `llm.py`. This will raise a `NameError` and crash the application when the fallback is triggered.

### CR-2: OverflowError on Key Exhaustion Telemetry
In `llm.py`'s `_push_telemetry` function, the status text is formatted using `int(self.cooldown_keys[key] - now)`. If an API key is permanently exhausted after reaching 10 strikes, its cooldown is set to `float('inf')`. Attempting to convert infinity to an integer will raise an `OverflowError`, which will crash the rate limit guard and the application.

### WR-1: Cache File Corruption Risk
In `pipeline.py`, the cache is saved progressively on each page extraction using `with open(cache_file, "w")`. If the process is interrupted or forcefully terminated while writing, the cache file will be overwritten with partial JSON data, corrupting the entire cache. An atomic write approach (e.g., writing to a temporary file and using `os.replace`) should be utilized to prevent data loss.

### WR-2: Global Pipeline Blocked by Single Key Failure
In `llm.py`'s `_report_failure`, a failure on a single key sets a penalty that updates `self.global_cooldown_until`. This forces all other healthy API keys to wait for the penalty duration, bottlenecking the entire pipeline whenever a single key encounters an isolated rate limit or server error.

### WR-3: Deadlock Risk on Telemetry Queue
In `llm.py`, `self.telemetry_queue.put(state)` is called inside `_push_telemetry` while holding `self.lock`. If the telemetry queue is a bounded queue and becomes full, the `put()` call will block indefinitely, causing the thread to hold the lock forever and deadlocking the entire rate limiter.

### IN-1: Unrotated Telemetry File Logger
The `telemetry_logger` in `llm.py` is configured with a basic `logging.FileHandler` writing to `telemetry.log`. In a long-running process, this file will grow unbounded. Consider using a `logging.handlers.RotatingFileHandler` to prevent disk space exhaustion.

### IN-2: Unbounded Context Window for Entity Resolution
In `pipeline.py`, the `resolve_entities` function sends the entire `raw_pages_log` to the LLM at once. For massive PDFs containing hundreds or thousands of pages, this string may exceed the token limit of the model or incur high token costs. A batching or chunking strategy for the log string is recommended.

### IN-3: Invalid JSON Penalizes Rate Limits
In `llm.py`, an `InvalidResponseError` (triggered by the model failing to output valid JSON) is treated as a failure that increments key strikes and triggers a global pause. Since model adherence failures are independent of API rate limits and server health, they should not exhaust keys or pause the entire pipeline.
