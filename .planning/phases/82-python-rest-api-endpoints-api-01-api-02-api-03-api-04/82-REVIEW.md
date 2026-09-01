---
phase: 82-python-rest-api-endpoints-api-01-api-02-api-03-api-04
reviewed: 2026-09-01T07:09:45Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/api/__init__.py
  - src/api/models.py
  - src/api/routes.py
  - src/api/server.py
  - src/main.py
findings:
  critical: 1
  warning: 3
  info: 3
  total: 7
status: issues_found
---

# Phase 82: Code Review Report

**Reviewed:** 2026-09-01T07:09:45Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

The API endpoints were reviewed at standard depth. A critical server-crashing bug was identified in the CORS configuration where `allow_origins=["*"]` cannot be used simultaneously with `allow_credentials=True`. A few warnings around unexpected data types causing 500 errors, hidden directory exposure, and improperly formatted HTTP exception details were also flagged.

## Narrative Findings (AI reviewer)

### CR-01: Invalid CORS Configuration Causes Server Startup Crash

**File:** `src/api/server.py:38-44`
**Issue:** FastAPI/Starlette's `CORSMiddleware` raises an `AssertionError` at server startup if `allow_origins=["*"]` is combined with `allow_credentials=True`. This completely breaks the server initialization.
**Fix:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Set to False if wildcard origins are required
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### WR-01: Stringified JSON passed to HTTPException detail

**File:** `src/api/routes.py:12`
**Issue:** `NOT_FOUND_DETAIL` is defined as a JSON string. FastAPI automatically serializes dictionary details to JSON. By passing a JSON string, the response will be a double-escaped string (e.g., `{"detail": "{\"error\": ...}"}`) rather than a proper JSON object payload.
**Fix:**
```python
NOT_FOUND_DETAIL = {"error": "Resource not found.", "solution": "Verify the endpoint URL and the resource ID."}
```

### WR-02: Exposure of Hidden Directories in List Houses Endpoint

**File:** `src/api/routes.py:27`
**Issue:** The `list_houses` endpoint iterates over all directories in `areas_root` and includes them as houses. It does not filter hidden directories (like `.git` or `.source_files`), which could leak internal folders.
**Fix:**
```python
    for entry in areas_root.iterdir():
        if entry.is_dir() and not entry.name.startswith("."):
            houses.append(HouseResponse(id=entry.name, name=entry.name))
```

### WR-03: Unhandled AttributeError on Malformed JSON Elements

**File:** `src/api/routes.py:48-50`
**Issue:** In `list_vault_files`, `list_timeline`, and `list_categories`, the code iterates over JSON arrays (`report_data.get("documents", [])`) and calls `.get(...)` directly on the elements. If an element is a string instead of a dict (e.g., due to malformed JSON), this raises an `AttributeError` which is not caught by `except ValidationError`, resulting in an unhandled 500 error.
**Fix:**
Add a type check before processing elements:
```python
    for doc in report_data.get("documents", []):
        if not isinstance(doc, dict):
            continue
        try:
```

### IN-01: Unused Variable 'tenants_path'

**File:** `src/api/routes.py:97`
**Issue:** `tenants_path` is defined but never used in the `list_categories` endpoint.
**Fix:** Remove the variable declaration.

### IN-02: Unused Variable 'pdf_files'

**File:** `src/main.py:55`
**Issue:** `pdf_files` is evaluated in `validate_target_directory` but never used.
**Fix:** Remove the variable declaration.

### IN-03: Unused Variable 'house_dir'

**File:** `src/main.py:353`
**Issue:** `house_dir` is instantiated in the main pipeline execution loop but never passed to any step.
**Fix:** Remove the unused variable declaration.
