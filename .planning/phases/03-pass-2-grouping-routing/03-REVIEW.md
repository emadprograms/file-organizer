---
status: "issues_found"
files_reviewed: 17
critical: 0
warning: 1
info: 1
total: 2
---

# Code Review: Phase 03 (Pass 2 Grouping and Routing)

## Summary
The phase 3 implementation successfully implements the boundary detection shrink loop and the hardcoded + LLM fallback routing logic. The code is well-structured and makes good use of Pydantic models for schema validation. Tests have been updated and provided.

There is a minor issue with mutable state in `routing.py` that should be addressed to prevent future bugs.

## Findings

### WR-1: Dictionary mutation hazard in routing logic
- **File:** `src/processing/routing.py`
- **Line:** ~60
- **Description:** `allowed_folders = CATEGORY_TO_FOLDERS.get(category, [])` returns a reference to the list in the global dictionary. If `"13_others"` is not in the list, `allowed_folders.append("13_others")` modifies the global `CATEGORY_TO_FOLDERS` dictionary. Currently, this code is safe only because all multi-match categories explicitly include `"13_others"`, but it's a silent trap for future modifications.
- **Recommendation:** Use `allowed_folders = list(CATEGORY_TO_FOLDERS.get(category, []))` or `allowed_folders = CATEGORY_TO_FOLDERS.get(category, []).copy()` to ensure you are modifying a local copy.

### IN-1: Exception handling in route_document swallows detail
- **File:** `src/processing/routing.py`
- **Line:** ~103
- **Description:** The `except Exception as e:` block inside the retry loop catches all exceptions and logs them as warnings. While this correctly triggers the fallback after 2 failures, it might hide `RateLimitError` or `google.genai.errors.APIError` issues that should ideally be propagated if they are fatal, or at least tracked differently.
- **Recommendation:** Consider explicitly catching `google.genai.errors.APIError` and standard validation errors from Pydantic, rather than a bare `Exception`, to avoid masking unexpected application bugs (like `KeyError` or `TypeError`).

## Next Steps
- Consider using `/gsd-code-review 3 --fix` to auto-resolve the warning.
