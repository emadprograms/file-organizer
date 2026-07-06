---
wave: 1
depends_on: []
files_modified:
  - src/core/utils.py
  - src/fs_utils.py
  - src/llm/llm.py
  - src/processing/routing.py
  - src/processing/grouping.py
autonomous: true
---

# Phase 10: Close gaps: Wire correct sanitize_filename and fix LLM 500 error handling

## Goal
Standardize `sanitize_filename` across the project to ensure file extensions are preserved while maintaining safety truncations. Implement a global LLM 500 error counter to abort the pipeline cleanly upon persistent failure, replacing localized fallback behaviors that previously produced partial or `Unassigned` output.

## Tasks

<task>
<read_first>
- src/core/utils.py
- src/fs_utils.py
- src/processing/organizer.py
</read_first>
<action>
1. Standardize `sanitize_filename` in `src/core/utils.py`:
   - Keep the existing `NFC` normalization and replacement of illegal characters `[/\\:*?"<>|]` with `_`.
   - Update the invisible control character removal to use the more robust `unicodedata.category(ch) not in ('Cc', 'Cf')` approach (from `fs_utils.py`).
   - Keep the multiple underscore collapse logic (`re.sub(r'_+', '_', sanitized)`).
   - Update the truncation logic so that it uses `os.path.splitext` to preserve the file extension when the string length exceeds `max_length`. Ensure it still respects string-based (character) length limits.
2. Delete the duplicate `sanitize_filename` function entirely from `src/fs_utils.py`.
3. Verify that `src/processing/organizer.py` relies solely on `src.core.utils.sanitize_filename` (it already does, but confirm no breakage).
</action>
<acceptance_criteria>
- `src/fs_utils.py` does not contain `def sanitize_filename`
- `src/core/utils.py`'s `sanitize_filename` explicitly uses `os.path.splitext` to preserve the file extension when truncating
- Calling `sanitize_filename("a"*250 + ".pdf", max_length=200)` returns a string ending in `.pdf` and with a total length of 200 characters
</acceptance_criteria>
</task>

<task>
<read_first>
- src/llm/llm.py
- src/processing/routing.py
- src/processing/grouping.py
</read_first>
<action>
1. In `src/llm/llm.py`:
   - Add `self.global_consecutive_500_errors = 0` to `LLMClient.__init__`.
   - In `_route_llm_call`, if an exception occurs and all providers fail with a 5xx/Timeout error, increment `self.global_consecutive_500_errors`.
   - If `self.global_consecutive_500_errors >= 5`, raise a new `LLMFailureError("Global 500 error limit reached. Aborting pipeline.")` instead of generic `RuntimeError`.
   - If any API call succeeds without an exception, reset `self.global_consecutive_500_errors = 0`.
2. In `src/processing/routing.py`:
   - Add `except LLMFailureError: raise` explicitly before the generic `except Exception as e:` block inside `route_document`, ensuring the global failure aborts the pipeline rather than falling back to `"13_others"`.
3. In `src/processing/grouping.py`:
   - Add `except LLMFailureError: raise` explicitly before the generic `except Exception as e:` block inside `process_with_shrink`, ensuring the global failure aborts the pipeline rather than triggering the chunk size shrink mechanism.
</action>
<acceptance_criteria>
- `src/llm/llm.py` increments a global 500 error counter and raises `LLMFailureError` when it hits 5 consecutive failures across the entire pipeline
- `src/processing/routing.py` explicitly raises `LLMFailureError` if encountered
- `src/processing/grouping.py` explicitly raises `LLMFailureError` if encountered
- A persistent sequence of 500 errors causes the script to abort (exit non-zero) instead of successfully generating partial output
</acceptance_criteria>
</task>

## Verification

- **Code Inspection:** Check `src/core/utils.py` for extension-aware truncation logic in `sanitize_filename`.
- **Code Inspection:** Ensure `fs_utils.py` no longer contains `sanitize_filename`.
- **Code Inspection:** Ensure `src/llm/llm.py` defines and increments the global 500 counter, resetting it on success.
- **Behavior Assertion:** Test throwing `LLMFailureError` manually inside the LLM client to confirm `routing.py` and `grouping.py` do not swallow it.

## must_haves

truths:
  - D-01: sanitize_filename in core/utils.py preserves the file extension when truncating, and duplicates are removed
  - D-02: LLMFailureError bubbles up through grouping and routing without being caught by Unassigned fallback blocks
  - D-03: LLMClient tracks global_consecutive_500_errors and aborts at a threshold
  - D-04: Failure states abort cleanly to allow resuming without manual cleanup of partial successes or Unassigned fallback files
prohibitions:
  - statement: Do not swallow LLMFailureError in grouping.py or routing.py
    status: resolved
    verification: Code review confirms `except LLMFailureError: raise` is present before `except Exception:` blocks

## Artifacts this phase produces

- `src.core.utils.sanitize_filename` (modified function signature/behavior)
- `src.fs_utils.sanitize_filename` (deleted)
- `LLMClient.global_consecutive_500_errors` (new class attribute)
