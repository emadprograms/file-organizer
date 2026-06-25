---
version: 1.0
wave: 1
depends_on: []
files_modified:
  - src/llm.py
  - tests/test_llm.py
autonomous: true
---

# Phase 07.5.1: Hybrid Cloud-First Vision Extraction with Local Overflow

## Goal
Bypass the cloud vision model's 15 RPM limit by implementing a hybrid approach that seamlessly falls back to a local model (overflow queue) when the cloud model hits rate limits or is in a cooldown period. 

## Requirements
- `PERF-01`: Bypassing Cloud Rate Limits
- `ARCH-02`: Hardware-Accelerated Metal Processing
- `ARCH-01`: Local MLX / llama.cpp Server Integration

## must_haves

### truths
- D-01: The system uses the cloud model for Pass 1a until rate limited at 15 tries/min.
- D-02: The system uses the local model for vision extraction during the 1-minute cooldown period after a 429.
- D-03: The system automatically switches back to the cloud model as soon as the rate limit window resets.
- D-04: The hybrid approach is strictly limited to Pass 1a.

## Artifacts this phase produces
- `tests/test_llm.py:test_state_management_purging`
- `tests/test_llm.py:test_extract_page_normal_flow`
- `tests/test_llm.py:test_extract_page_overflow_flow`
- `tests/test_llm.py:test_extract_page_cooldown_flow`
- `tests/test_llm.py:test_extract_page_resumption_flow`

## Tasks

```xml
<task>
  <read_first>
    - src/llm.py
    - tests/test_llm.py
  </read_first>
  <action>
    Update `GLOBAL_RPM_LIMIT` in `GemmaClient` (`src/llm.py`) from `10` to `15` to match the exact cloud provider rate limit.
    
    Add the following tests to `tests/test_llm.py` to validate the state tracking and Execution Flow:
    1. `test_state_management_purging`: Verify that calling `_get_client_and_key` purges timestamps older than 65 seconds from `GemmaClient.global_rpm_tracker`.
    2. `test_extract_page_normal_flow`: Verify that when `len(global_rpm_tracker) < 15`, `extract_page` calls the cloud mock (`_extract_text_with_gemini`) and NOT the local mock (`_extract_text_with_qwen`).
    3. `test_extract_page_overflow_flow`: Mock the cloud call `_extract_text_with_gemini` to raise a `429 Too Many Requests` error. Verify that `extract_page` catches it, sets a penalty via `_report_failure`, and successfully returns the result from the local mock (`_extract_text_with_qwen`).
    4. `test_extract_page_cooldown_flow`: Force `GemmaClient.global_cooldown_until` to be in the future (e.g., `time.time() + 60`). Verify that `extract_page` immediately calls the local mock (`_extract_text_with_qwen`) WITHOUT attempting the cloud mock (because `_get_client_and_key(..., no_wait=True)` returns `None`).
    5. `test_extract_page_resumption_flow`: Simulate advancing the clock past `global_cooldown_until` and clearing the `global_rpm_tracker`. Verify that the next call to `extract_page` correctly targets the cloud mock (`_extract_text_with_gemini`) again.
  </action>
  <acceptance_criteria>
    - `src/llm.py` contains `GLOBAL_RPM_LIMIT = 15`.
    - `pytest tests/test_llm.py` passes all tests.
    - `tests/test_llm.py` contains `def test_extract_page_normal_flow`.
    - `tests/test_llm.py` contains `def test_extract_page_overflow_flow`.
    - `tests/test_llm.py` contains `def test_extract_page_cooldown_flow`.
    - `tests/test_llm.py` contains `def test_extract_page_resumption_flow`.
  </acceptance_criteria>
</task>
```
