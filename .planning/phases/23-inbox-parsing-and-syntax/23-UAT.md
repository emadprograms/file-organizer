---
status: complete
phase: 23-inbox-parsing-and-syntax
source: [23-01-SUMMARY.md, 23-02-SUMMARY.md]
started: 2026-07-20T16:15:00Z
updated: 2026-07-20T16:47:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Process specific unclassified PDF
expected: Command allows processing a specific file and completes without throwing errors about missing categorized copies.
result: pass

### 2. Infer missing data with majority voting
expected: When categorization report contains missing data flags ('U'), the system correctly infers House ID and date using majority voting from the data.
result: pass

### 3. Duplicated House IDs in different areas
expected: When processing a file with a House ID that exists in multiple areas, the system throws a conflict error.
result: pass

### 4. Tenant resolution and group mapping
expected: The system successfully canonicalizes a tenant name against YAML configs and maps group numbers to correctly zero-padded folders (e.g. "01 - Admin") based on FOLDER_PREFIXES.
result: issue
reported: "if it couldn't identify U then that is a problem. U is not a name hint, it is unidentified. the way the program handles this is weird? wtf?"
severity: major

### 5. Append mode invalid syntax fallback
expected: When a file with invalid inbox syntax is parsed in append mode, the system renames the file indicating a validation failure and optionally triggers LLM resolution steps.
result: pass

### D1. Parser correctly extracts 5 positional arguments and title
expected: Parser correctly extracts 5 positional arguments and title
result: pass
source: automated
coverage_id: D1

### D2. Parser validates the group field restricts to 1-13, G, U
expected: Parser validates the group field restricts to 1-13, G, U
result: pass
source: automated
coverage_id: D2

## Summary

total: 7
passed: 6
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "The system successfully canonicalizes a tenant name against YAML configs and maps group numbers to correctly zero-padded folders (e.g. '01 - Admin') based on FOLDER_PREFIXES."
  status: failed
  reason: "User reported: if it couldn't identify U then that is a problem. U is not a name hint, it is unidentified. the way the program handles this is weird? wtf?"
  severity: major
  test: 4
  root_cause: "resolve_tenant hardcodes returning 'U' when the hint is 'U'. It does not attempt to infer the missing tenant from the document or report."
  artifacts:
    - path: "src/inbox/resolver.py"
      issue: "resolve_tenant early exit on 'U'"
  missing:
    - "Update infer_missing_data and resolve_tenant to extract and canonicalize the tenant name from the document when the tenant hint is 'U', similar to how the house ID and date are inferred."
  debug_session: "manual-diagnosis"
