---
phase: 05
reviewers: [codex]
reviewed_at: 2026-06-23T18:55:01Z
plans_reviewed: [05-PLAN.md]
---

# Cross-AI Plan Review — Phase 05

## Codex Review

**Summary**
The Phase 05 plan effectively targets critical formatting and data integrity issues. It appropriately shifts directory creation to just-in-time generation to eliminate empty folders, ensures lexicographical sorting of Arabic categories, and introduces stricter exception handling to prevent silent pipeline failures. However, there are significant risks regarding the broadness of the exception handling and the destructive nature of the fallback mechanism when validation fails.

**Strengths**
- Just-in-time (JIT) directory creation correctly prevents filesystem clutter.
- Switching to zero-padded prefixes with underscores solves the OS lexicographical sorting issues while maintaining clean code.
- Explicitly instructing the LLM to retain non-primary identities is a robust approach to preventing data loss during entity resolution.
- Ensuring exceptions are not silently swallowed prevents insidious silent data corruption or loss.

**Concerns**
- **HIGH:** Catching a broad `Exception` in `process_single_page` (Task 5) is dangerous because it will swallow structural code bugs (e.g., `AttributeError`, `KeyError`, `SyntaxError`) and silently convert them to `UNKNOWN` document categories, masking real code defects. It should specifically catch `LLMFailureError` or known extraction exceptions.
- **HIGH:** The fallback classification returned upon an exception (Task 5) hardcodes `house_number="UNKNOWN"`. If an `other_letters` page lacks a resident name, it triggers retries (Task 6), eventually throwing an `LLMFailureError`. This means a valid page with a known house number but no resident will completely lose its house routing and be orphaned to `UNKNOWN/UNKNOWN/other_letters`. The fallback must attempt to preserve the house number if it was already known or extracted.
- **MEDIUM:** Task 2 (ARABIC-02) uses an underscore separator (`01_`), which contradicts the Roadmap's success criteria (`01. `). While the Context explicitly decides on the underscore, the discrepancy should be updated in the Roadmap to prevent QA validation failures.
- **LOW:** Removing the `other_letters` exemption from `NONE_EXPECTED_CATEGORIES` (Task 6) will cause purely blank pages to unnecessarily exhaust the `max_attempts` circuit breaker, wasting API calls and time.

**Suggestions**
- Update Task 5 to catch only `LLMFailureError` (or a specific subclass of exceptions related to LLM/validation) in `process_single_page` rather than a bare `Exception`.
- Update Task 5 to ensure that the fallback mechanism can inherit the `house_number` from the current batch/context if available, rather than hardcoding `"UNKNOWN"`.
- Update the `ROADMAP.md` ARABIC-02 success criteria to reflect the `01_` separator decision made in `05-CONTEXT.md`.
- Consider a pre-check for completely blank pages before sending them to the LLM to avoid wasting `max_attempts` due to the strict name requirements of Task 6.

**Risk Assessment**
HIGH. While the formatting changes are safe, the combination of enforcing retries on `other_letters` (Task 6) and a destructive fallback mechanism (Task 5) that drops the house number guarantees that generic letters will be permanently orphaned. Additionally, the broad `Exception` catch risks hiding unrelated pipeline failures.

---

## Consensus Summary

### Agreed Strengths
- JIT folder generation reduces visual clutter.
- Zero-padding fixes Windows sorting issues.

### Agreed Concerns
- Broad exception catching in `process_single_page` hides actual code bugs. (HIGH)
- The fallback mechanism drops the `house_number`, orphaning documents that fail validation (e.g. valid `other_letters` missing a resident name). (HIGH)

### Divergent Views
- None (single reviewer).
