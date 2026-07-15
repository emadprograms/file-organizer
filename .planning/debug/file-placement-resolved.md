# Debug Session: File Placement Bugs

**Status:** resolved
**Date:** 2026-07-15

## Symptoms
1. `_tenants.yaml` gets created in a separate folder from `_categorized.pdf`
2. `_report.json` not moved to `.source_files/` directory
3. `_routed.json` (reconciliation manifest) missing from `.source_files/`

## Root Causes

### Bug 1: `_tenants.yaml` wrong directory
- `process_cleaning_phase()` received `house_dir` (= `output_dir / house_id`, e.g. `pdfs/1273`)
- But the PDF lived in `target_dir` (e.g. `pdfs/1273 - TenantName` when pre-renamed)
- YAML was written to `house_dir` which was a **different** folder from the PDF

### Bug 2: `_report.json` not moved
- `target_dir` was reassigned to `house_dir` on line 201 before the JSON glob
- The glob scanned `house_dir` instead of the **original** `target_dir` where `_report.json` lived

### Bug 3: `_routed.json` missing
- `reconciliation.py:31` writes using `full_house_id` (e.g. `"1273 - TenantName"`)
- `main.py:195` looked for it using `house_id` (e.g. `"1273"`)
- Name mismatch: file existed but was never found

## Fixes Applied

### Fix 1 — `main.py:290`
Pass `target_dir` instead of `house_dir` to `process_cleaning_phase()` so YAML is written alongside the PDF.

### Fix 2 — `main.py:198,217-225`
Save `original_target_dir` before reassignment. Use it for the JSON move glob, with fallback to house_dir.

### Fix 3 — `main.py:195`
Use `full_house_id` in the routed path lookup to match what reconciliation actually writes.
