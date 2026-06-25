---
wave: 1
depends_on: []
files_modified:
  - src/llm.py
  - tests/test_llm.py
autonomous: true
requirements:
  - D-01
  - D-02
  - D-03
  - D-04
  - D-05
---

# Phase 07.5.1: Hybrid Cloud-First Vision Extraction with Local Overflow

## Goal
Implement a hybrid Cloud-First OCR architecture in `Pass 1a`. The system must use `gemma-4-26b-a4b-it` as the primary vision model. When the rate limit is hit, execution should non-blockingly overflow to the local `qwen2.5vl:7b` model during the cooldown window, and snap back to the cloud model once the cooldown expires.

## Tasks

```xml
<task>
  <read_first>
    - src/llm.py
    - .planning/phases/07.5.1-hybrid-cloud-first-vision-extraction-with-local-overflow/07.5.1-CONTEXT.md
  </read_first>
  <action>
    In `src/llm.py`, replace all occurrences of `gemini-1.5-flash` with `gemma-4-26b-a4b-it` to restore the preferred cloud model logic.
    Update `_extract_text_with_gemini`, `classify_page`, `check_name_match`, and any console logging statements that reference the old model name.
  </action>
  <acceptance_criteria>
    `grep "gemini-1.5-flash" src/llm.py` returns no matches.
    `grep "gemma-4-26b-a4b-it" src/llm.py` returns multiple matches in `_extract_text_with_gemini`, fallback logic, and logging.
  </acceptance_criteria>
</task>

<task>
  <read_first>
    - src/llm.py
    - .planning/phases/07.5.1-hybrid-cloud-first-vision-extraction-with-local-overflow/07.5.1-CONTEXT.md
  </read_first>
  <action>
    In `src/llm.py`, resolve the artificial bottleneck where the global RPM limit is hardcoded to 15 regardless of the number of active API keys (D-05).
    Remove the class attribute `GLOBAL_RPM_LIMIT = 15`.
    In `GemmaClient.__init__`, initialize an instance variable `self.global_rpm_limit = 15 * len(self.api_keys)`.
    Update `_get_client_and_key` to use `self.global_rpm_limit` instead of `self.GLOBAL_RPM_LIMIT` when checking `len(GemmaClient.global_rpm_tracker)`.
  </action>
  <acceptance_criteria>
    `GLOBAL_RPM_LIMIT = 15` is no longer a class attribute in `src/llm.py`.
    `self.global_rpm_limit = 15 * len(self.api_keys)` exists in `__init__`.
    `_get_client_and_key` properly scales its RPM capacity dynamically based on available keys.
  </acceptance_criteria>
</task>

<task>
  <read_first>
    - src/llm.py
    - .planning/phases/07.5.1-hybrid-cloud-first-vision-extraction-with-local-overflow/07.5.1-CONTEXT.md
  </read_first>
  <action>
    In `src/llm.py`, implement explicit state management for the 65-second cooldown and non-blocking fallback (D-04).
    1. Ensure `extract_page` implements a strict try-except block that catches 429 errors.
    2. Ensure that upon catching a 429 error, a timestamp is set for the cooldown (e.g., `current_time + 65` seconds).
    3. Ensure that if `current_time < cooldown_expiry`, `extract_page` skips the cloud attempt and immediately invokes `_extract_text_with_qwen` without any intervening `time.sleep()` calls.
    4. Implement logic to clear the cooldown state and "snap back" to the cloud model once the 65 seconds have elapsed.
    5. Add clear, distinct logging statements for model transitions (Cloud -> Local and Local -> Cloud) to ensure visibility.
  </action>
  <acceptance_criteria>
    `extract_page` has a strict try-except block catching 429 errors.
    The 65-second cooldown is explicitly tracked and enforced using timestamps.
    Transitions between Cloud and Local execution are clearly logged.
    `extract_page` does not contain any `time.sleep()` statements.
  </acceptance_criteria>
</task>

<task>
  <read_first>
    - src/llm.py
    - tests/test_llm.py
  </read_first>
  <action>
    In `tests/test_llm.py`, implement comprehensive unit and end-to-end tests for the fallback logic and rate limit handling.
    1. Add tests with synthetic API responses simulating a 429 error and verifying that the fallback to the local model happens immediately.
    2. Add tests verifying that the system remains in the local fallback mode during the 65-second cooldown window.
    3. Add tests verifying that the system correctly transitions back to the cloud model after the cooldown expires.
    4. Ensure the dynamic scaling of RPM based on the number of keys is tested.
  </action>
  <acceptance_criteria>
    `test_llm.py` contains explicit tests for 429 error handling and immediate fallback.
    Tests verify the 65-second cooldown window state management.
    Tests verify the "snap back" to the cloud model after the cooldown.
    Tests pass without errors.
  </acceptance_criteria>
</task>
```

## Verification
- Must have: Qwen local fallback executes immediately upon rate limiting the Gemma API without hanging the main thread.
- Must have: Model instances point to `gemma-4-26b-a4b-it`.
- Must have: RPM limit scales linearly with configured API keys.
- Must have: Cooldown state is correctly managed and transitions are logged.
- Must have: Fallback and cooldown logic is covered by unit/E2E tests.

## Artifacts this phase produces
- No new classes or file paths are created. This phase refactors existing internal methods within `src/llm.py` and adds tests to `tests/test_llm.py`.
