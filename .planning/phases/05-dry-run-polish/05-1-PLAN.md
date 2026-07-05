---
wave: 1
depends_on: []
files_modified:
  - src/processing/organizer.py
  - src/organize.py
autonomous: true
---

# Plan 1: Core Dry Run Support & CLI Output

## Objective
Implement the `--dry-run` flag across the pipeline to simulate folder creation, PDF extraction, and reconciliation without executing physical file writes. Add `rich`-based terminal output to visualize the planned actions.

## Artifacts this phase produces
- **CLI Flags**: `--dry-run` added to `src/organize.py`
- **Function Parameters**: `dry_run: bool = False` added to `FileOrganizer.organize` and `run_reconciliation` in `src/processing/organizer.py`

## Requirements
- DIFF-01

## Tasks

1. Update `FileOrganizer` to respect `--dry-run`
   <read_first>
   - src/processing/organizer.py
   </read_first>
   <action>
   Add `dry_run: bool = False` parameter to `FileOrganizer.organize(...)` and `run_reconciliation(...)` in `src/processing/organizer.py`. Wrap `os.makedirs(target_dir, exist_ok=True)` and `extract_pdf_segment(...)` in `if not dry_run:` blocks. Add a `logger.info(...)` in the `else` block to log what would have been extracted. Wrap the `manifest.json` writing block in `run_reconciliation` with `if not dry_run:` and add an `else` block logging that manifest writing is skipped.
   </action>
   <acceptance_criteria>
   - `src/processing/organizer.py` defines `dry_run: bool = False` in both methods.
   - `os.makedirs`, `extract_pdf_segment`, and `manifest` dumping are conditionally bypassed when `dry_run` is true.
   </acceptance_criteria>

2. Add `--dry-run` CLI flag
   <read_first>
   - src/organize.py
   </read_first>
   <action>
   In `src/organize.py` `get_parser()`, add `--dry-run` flag using `action="store_true"` and `help="Preview the pipeline output without writing physical files or PDFs."`.
   </action>
   <acceptance_criteria>
   - `python src/organize.py -h` displays `--dry-run`.
   </acceptance_criteria>

3. Conditionally skip or load checkpoints in `organize.py`
   <read_first>
   - src/organize.py
   </read_first>
   <action>
   In `src/organize.py` `main()`, pass `dry_run=args.dry_run` to `FileOrganizer.organize` and `run_reconciliation`. If `args.dry_run` is true:
   - Do NOT open/write to `output_json_path` for `cleaned.json` and `grouped.json`.
   - If the checkpoint files (`cleaned.json` / `grouped.json`) already exist at their expected paths, read and load them to populate `cleaned_pages` and `documents` respectively, bypassing the LLM processing loops to save time.
   </action>
   <acceptance_criteria>
   - When running with `--dry-run`, no new `.json` checkpoints are written.
   - When running with `--dry-run` and checkpoints exist, `cleaned_pages` or `documents` are loaded from disk and LLM calls are skipped.
   </acceptance_criteria>

4. Implement `rich` visualization for dry run
   <read_first>
   - src/organize.py
   </read_first>
   <action>
   In `src/organize.py` `main()`, when `args.dry_run` is true, after processing is complete, use `rich.console.Console`, `rich.tree.Tree`, and `rich.table.Table` to output a tabular summary of the actions and a hierarchical Tree view of the generated file structure (`House ID` -> `Tenant` -> `Category` -> `PDFs`). Ensure Windows Arabic encoding works by setting `sys.stdout.reconfigure(encoding='utf-8')` if `sys.platform == 'win32'`.
   </action>
   <acceptance_criteria>
   - Running with `--dry-run` prints a `rich` Table and Tree to the terminal.
   - Arabic characters render correctly in the console without throwing `UnicodeEncodeError`.
   </acceptance_criteria>

## Verification
- Run `python src/organize.py ./pdfs/1273 --dry-run` and verify `output/1273` is NOT created, but terminal output shows the expected folder structure and files.

## must_haves
  truths:
    - "`--dry-run` flag shows full pipeline output (folder structure, file names) without writing any files"
    - "D-01: Both a tree-like folder view and a tabular summary should be presented in the terminal during a dry run"
    - "D-02: Dry run reads existing checkpoints to save API costs if they exist, but bypasses writing `manifest.json` and intermediate `.json` checkpoints"
  prohibitions: []
