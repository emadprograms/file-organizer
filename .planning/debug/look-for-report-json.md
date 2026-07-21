---
status: resolved
trigger: "tell the app to look for _report.json inside the .source_files/ from now on. always."
created: 2026-07-21T16:18:00Z
updated: 2026-07-21T16:22:00Z
---

## Symptoms
- **Expected behavior**: In `create` mode, the app should bypass categorization and re-running if `_report.json` is already in `.source_files/`.
- **Actual behavior**: It checks for `_report.json` only in the root directory. Since the file was moved to `.source_files/` in the previous run, it doesn't find it, re-runs LLM categorization if the raw PDF is present, and crashes with an IndexError on line 536 of main.py if the raw PDF is missing.
- **Error messages**: `IndexError: list index out of range` at `list(target_dir.glob(f"{house_id}_report*.json"))[0]`
- **Timeline**: Occurs when re-running `create` mode on an already processed and organized folder.
- **Reproduction**: Run `main.py create <already_created_folder>` where `.source_files/` exists and contains the report JSON.

## Current Focus
hypothesis: "The pipeline expects `_report.json` and `_categorized.pdf` to be in `target_dir` directly. Since previous runs move them to `.source_files/`, subsequent runs either incorrectly fail validation (if raw PDF is missing) or regenerate them."
next_action: resolve

## Evidence
- timestamp: 2026-07-21T16:18:00Z
  observation: "User reported the pipeline looks in root dir for _report.json instead of .source_files/."
- timestamp: 2026-07-21T16:21:00Z
  observation: "Confirmed that glob patterns in main.py and exist checks in categorization.py do not include .source_files/."

## Eliminated
- hypothesis: "The bug is solely in main.py line 536"
  reason: "The issue affects `validate_target_directory` in main.py, line 315 in main.py, and `process_unclassified_pdf` in categorization.py."

## Resolution
root_cause: "The `create` mode checks for existing `_report.json` and `_categorized.pdf` files strictly in `target_dir`, failing to account for them being moved to `.source_files/` after a successful run."
fix: "Updated glob patterns in `src/main.py` (lines 51, 52, 315, 536) and `path.exists()` checks in `src/categorization/categorization.py` (line 61) to look in both `target_dir` and `target_dir / '.source_files'`."
verification: "Tested `main.py create test_dir` with dummy files in `.source_files/`. The script correctly bypassed categorization and successfully read the files from `.source_files/` without raising IndexError."
files_changed: 
  - src/main.py
  - src/categorization/categorization.py
