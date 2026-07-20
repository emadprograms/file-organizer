---
phase: 23
reviewers: [claude]
reviewed_at: 2026-07-20T15:02:41Z
plans_reviewed: [23-01-PLAN.md, 23-02-PLAN.md]
---

# Cross-AI Plan Review — Phase 23

## the agent Review

## Summary
The plans provide a solid separation of concerns, successfully splitting pure parsing (Plan 1) from filesystem and LLM side-effects (Plan 2). Plan 1 correctly models the 5-part space-separated syntax using Pydantic. Plan 2 intelligently coordinates inference and resolution logic. However, Plan 2 has several critical integration flaws: it fails to account for `process_unclassified_pdf` operating on a directory rather than a single file, it doesn't specify correctly locating the tenant YAML file inside the resolved area directory, and its mapping of the group number to `FOLDER_PREFIXES` lacks reverse-lookup specifics.

## Strengths
- **Pure Parsing (Plan 1)**: Isolating the string splitting and validation into a pure function `parse_filename_syntax` that returns a Pydantic model is excellent for testability.
- **Strict Group Constraints (Plan 1)**: Using Pydantic validators for the `group` field ('1'-'13', 'G', 'U') precisely enforces Decision D-06 (`src/core/schemas.py`).
- **Conflict Handling (Plan 2)**: Creating a specific `ConflictError` for area resolution gracefully satisfies D-11 by enabling the CLI hook to rename the file accurately.
- **Majority Vote Logic (Plan 2)**: Utilizing `collections.Counter` on the list of page dicts in `_report.json` correctly leverages the output structure of `process_unclassified_pdf` (`src/categorization/categorization.py:165`).

## Concerns
- **HIGH: `process_unclassified_pdf` Signature Mismatch**: Plan 2 says to call `process_unclassified_pdf` to generate `_report.json` for a specific file. However, `categorization.py:16` shows `process_unclassified_pdf(target_dir: Path, llm_client: Any)`. It iterates over `target_dir.glob("*.pdf")`. Passing the inbox path will process *all* PDFs in the inbox, which is dangerous in a listener loop and could cause race conditions or duplicate processing.
- **HIGH: Incorrect `target_dir` for Tenant YAML**: Plan 2 says to use `yaml_loader.py` to load tenants. `load_tenant_config` (`src/tenant_config/yaml_loader.py:10`) expects the `target_dir` containing the `.source_files` directory. This YAML file lives in the specific house folder (e.g., `areas_root/Area_ID/House_ID/`), NOT the inbox. Plan 2 does not enforce resolving the area *before* resolving the tenant so the correct directory can be passed.
- **MEDIUM: `FOLDER_PREFIXES` Reverse Lookup**: Plan 2 mentions mapping the `group` value ('1'-'13') to `FOLDER_PREFIXES` in `src/routing/config.py`. However, `FOLDER_PREFIXES` (`src/routing/config.py:28`) maps Arabic folder names (keys) to string prefixes like `"01"`, `"02"` (values). The logic must explicitly format the user's input (e.g., `f"{int(group):02d}"`) and reverse-lookup the key to get the correct folder name.
- **LOW: Missing `llm_client` in Append Mode**: Plan 2 updates `src/main.py` `run_append_mode` to call `infer_missing_data` (which calls `process_unclassified_pdf`) and `resolve_tenant` (which calls `canonicalize_with_llm`). Both of these require an initialized `LLMClient`, but Plan 2 doesn't mention instantiating one inside `run_append_mode` like `main()` does for `create` mode.
- **LOW: Unsafe String Stripping (Plan 1)**: If `parse_filename_syntax` uses `.strip(".pdf")`, it will strip individual characters rather than the extension.

## Suggestions
- **Refactor `process_unclassified_pdf` or wrap it**: Update Plan 2 to either temporarily isolate the target PDF in a scratch directory before calling `process_unclassified_pdf`, or refactor `categorization.py` to accept an optional specific `pdf_path`.
- **Enforce Resolution Order**: Update Plan 2 to strictly order resolutions: 1. `infer_missing_data` -> 2. `resolve_area` -> 3. Construct `house_dir` -> 4. `resolve_tenant` using the `house_dir` as `target_dir`.
- **Reverse Lookup Logic**: Specify in Plan 2 that `resolve_group_mode` must zero-pad the group integer to 2 digits and find the dictionary key in `FOLDER_PREFIXES` that has this string value.
- **Initialize LLM Client**: Explicitly add a task to initialize `LLMClient` in `run_append_mode` inside `src/main.py` so it can be passed to the resolver functions.
- **Strip extensions securely**: In Plan 1, specify using `filename.lower().endswith(".pdf")` and `filename[:-4]` rather than `strip(".pdf")`.

## Risk Assessment
- **Risk Level**: HIGH
- **Justification**: While the design is conceptually sound, the integration issues in Plan 2 (specifically calling a directory-wide processing function in a listener loop and passing the wrong directory for YAML loading) will cause the application to crash or behave unpredictably in the FS-UI append mode. These integration specifics must be corrected before execution.

---

## Consensus Summary

### Agreed Strengths
- Pure Parsing isolation
- Strict Group Constraints
- Conflict Handling for Areas

### Agreed Concerns
- **HIGH:** `process_unclassified_pdf` signature mismatch (expects directory, not file)
- **HIGH:** Incorrect `target_dir` for Tenant YAML loading

### Divergent Views
N/A - Only one reviewer.
