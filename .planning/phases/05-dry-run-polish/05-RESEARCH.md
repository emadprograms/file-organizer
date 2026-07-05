# Phase 5: Dry Run & Polish - Research

**Research Date:** 2026-07-05
**Goal:** Answer "What do I need to know to PLAN this phase well?"

## 1. Codebase Interventions

To implement the `--dry-run` feature cleanly, the following modules must be modified:

### A. CLI & Entry Point (`src/organize.py`)
- **Flag Addition:** Add a `--dry-run` boolean flag using `action="store_true"` in `get_parser()`.
- **Checkpoint Bypassing:** Modify the `main()` function:
  - If `--dry-run` is active and checkpoints (`cleaned.json`, `grouped.json`) *exist*, **read** them (saves LLM cost).
  - If `--dry-run` is active and checkpoints *do not exist*, run the processing passes but **skip writing** the resulting data to `.json` files.
- **Manifest Bypassing:** Skip saving the `1273_manifest.json` file during a dry run or pass the `dry_run` flag into `run_reconciliation` to prevent it from calling `json.dump(...)` to the disk.

### B. File Organizer (`src/processing/organizer.py`)
- **Skip Physical Writes:** Update `FileOrganizer.organize(...)` to accept the `dry_run: bool` parameter. 
- **Bypass operations:**
  - Wrap `os.makedirs(target_dir, exist_ok=True)` in a `if not dry_run:` block.
  - Wrap `extract_pdf_segment(...)` in a `if not dry_run:` block.
- **Retain Logic:** Continue generating `target_dir` and `filename` combinations so the complete output paths can be collected and visualized in the dry run report. 

### C. Visualization & Output Presentation
- Use the `rich` library (already in the stack) to build the dry run output.
- **Tabular Summary:** Use `rich.table.Table` to display a summary of actions (e.g., File Name, Tenant, Pages, Topic).
- **Tree View:** Use `rich.tree.Tree` to display the planned folder hierarchy (`House ID/` -> `Tenant 2020-2022/` -> `5_contract/` -> `2020-01-01 - العقد.pdf`).

## 2. Testing Strategy

### A. End-to-End Test (`tests/test_e2e.py`)
- The file `tests/test_e2e.py` is currently empty and needs to be implemented.
- **Goal:** Run the entire pipeline with `--dry-run` over the real `1273_report.json` and `1273_categorized.pdf` artifacts.
- **Setup Note:** The test data is currently sitting in `pdfs/` (`pdfs/1273_categorized.pdf` & `pdfs/1273_report.json`), but the CLI's `validate_target_directory` expects them *inside* the target directory (e.g., `pdfs/1273/`). The test needs to copy these files into a temporary directory structure mimicking the expected `pdfs/1273/` layout.
- **Verification:**
  - Assert that `output/` directory remains completely empty (or contains no newly generated PDFs or manifests) after the dry run completes.
  - Assert that the command exits successfully (`return code 0`).
  - Capture standard output (`capsys`) and verify that tree structures and target filenames appear in the log/console.

### B. Arabic Encoding on Windows
- Windows command prompts (cmd/PowerShell) often default to `cp1252` encoding, which garbles Arabic text (`cp1256` or `utf-8` needed).
- `rich` usually handles console encoding gracefully, but as a fallback/failsafe for standard logging or testing, you might need to ensure `sys.stdout.reconfigure(encoding='utf-8')` is evaluated if the platform is Windows, or rely on `PYTHONIOENCODING=utf8`. Tests should explicitly verify that Arabic characters in filenames pass through `utils.sanitize_filename()` safely and display without raising `UnicodeEncodeError`.

### C. Error Path Coverage
- Enhance existing `test_cli.py` or `test_pipeline.py` to cover:
  - **Missing Files:** Already partially covered in `test_cli.py` (`test_validate_target_directory_missing_pdf`). Ensure missing `_report.json` is fully tested.
  - **Malformed JSON:** Add a test verifying `process_cleaning_phase` or the main execution fails gracefully if the provided JSON is structurally invalid.
  - **LLM Failures:** Add unit tests mocking `LLMClient.generate_content` to simulate a `500 Server Error` loop hitting the max retry limit, ensuring the pipeline halts and reports appropriately.

## 3. Recommended Plan Steps

1. **Plan 1: `FileOrganizer` & `run_reconciliation` dry-run updates**
   - Update `src/processing/organizer.py` to accept and respect `dry_run` boolean flags. Skip OS modifications (`makedirs`, `extract_pdf_segment`, manifest writing) but return the mapped structure.
2. **Plan 2: Main pipeline dry-run integration & visualization**
   - Update `src/organize.py` to accept `--dry-run`, bypass checkpoint writing if active, and print the `rich.tree.Tree` and `rich.table.Table` visualization using the data returned by the organizer.
3. **Plan 3: E2E and Edge Case Testing**
   - Implement `tests/test_e2e.py` for the dry run.
   - Implement test coverage for malformed JSON and simulated LLM failure paths. 
   - Ensure Arabic encoding on Windows console is handled gracefully.
