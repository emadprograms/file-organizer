---
wave: 2
depends_on:
  - 05-1-PLAN.md
files_modified:
  - tests/test_e2e.py
  - tests/test_pipeline.py
  - tests/test_llm.py
  - tests/test_cli.py
autonomous: true
---

# Plan 2: End-to-End Tests & Polish

## Objective
Implement end-to-end tests for the `--dry-run` mode and ensure edge cases (malformed JSON, LLM failures) are thoroughly covered and handled gracefully.

## Artifacts this phase produces
- **New Files**: `tests/test_e2e.py`
- **Functions**: `test_dry_run_end_to_end` in `test_e2e.py`
- **Functions**: `test_validate_target_directory_missing_json` in `tests/test_cli.py`
- **Functions**: `test_malformed_json_graceful_failure` in `tests/test_pipeline.py`
- **Functions**: `test_llm_500_max_retries_halts` in `tests/test_llm.py`

## Requirements
- DIFF-01

## Tasks

1. Implement `test_dry_run_end_to_end`
   <read_first>
   - tests/test_e2e.py
   - src/organize.py
   </read_first>
   <action>
   Create `tests/test_e2e.py` with function `test_dry_run_end_to_end(tmp_path)`. Setup test fixture: create `tmp_path / "1273"`, and copy `pdfs/1273_categorized.pdf` and `pdfs/1273_report.json` to this directory. Execute `subprocess.run(["python", "-m", "src.organize", str(tmp_path / "1273"), "--dry-run"], env={"PYTHONIOENCODING": "utf8", **os.environ}, capture_output=True, text=True)`. Assert that `result.returncode == 0`, output directory doesn't exist or is empty, and `result.stdout` contains indicators from the `rich` table/tree.
   </action>
   <acceptance_criteria>
   - `pytest tests/test_e2e.py` passes.
   - Test proves that `--dry-run` produces output but modifies no files.
   </acceptance_criteria>

2. Test missing input files handling
   <read_first>
   - tests/test_cli.py
   - src/organize.py
   </read_first>
   <action>
   Update `tests/test_cli.py` (or create if it doesn't exist) to add `test_validate_target_directory_missing_json(tmp_path)`. Create a test directory with a valid PDF but without the corresponding `_report.json`. Assert that `validate_target_directory` (or the main flow) gracefully raises the appropriate error (e.g., `FileNotFoundError` or custom error) and exits cleanly.
   </action>
   <acceptance_criteria>
   - `pytest tests/test_cli.py` passes.
   - Missing `_report.json` is gracefully caught by validation.
   </acceptance_criteria>

3. Test malformed JSON handling
   <read_first>
   - tests/test_pipeline.py
   - src/organize.py
   </read_first>
   <action>
   Update `tests/test_pipeline.py` (or create if it doesn't exist) to add `test_malformed_json_graceful_failure(tmp_path)`. Create a test directory with a valid PDF but a syntactically invalid `_report.json`. Run the CLI main flow or the parsing function directly, and assert that it gracefully catches the JSON decode error / pydantic validation error, logs an error, and exits with a non-zero status code rather than spewing an unhandled stack trace.
   </action>
   <acceptance_criteria>
   - Malformed JSON inputs cause a graceful non-zero exit and appropriate error log, rather than unhandled exception.
   </acceptance_criteria>

4. Test LLM 500 error max retries halt
   <read_first>
   - tests/test_llm.py
   - src/processing/llm.py
   </read_first>
   <action>
   Update `tests/test_llm.py` (or create if it doesn't exist) to add `test_llm_500_max_retries_halts()`. Use `unittest.mock.patch` on `LLMClient.generate_content` (or the underlying `google` client) to continuously raise a 500 Server Error. Invoke a method that calls the LLM (like the grouping or canonicalization loop) and assert that it correctly halts or raises the max-retries exceeded error without looping infinitely.
   </action>
   <acceptance_criteria>
   - `pytest tests/test_llm.py` passes and completes quickly.
   - Max retry limit logic is verified to prevent infinite loops.
   </acceptance_criteria>

## Verification
- Run `pytest tests/` and verify all tests pass.

## must_haves
  truths:
    - "End-to-end test with real `1273_report.json` and `1273_categorized.pdf` produces correct output via dry-run"
    - "Arabic filenames render correctly on Windows"
    - "Missing `_report.json` input is gracefully handled and logged"
    - "Malformed JSON inputs fail gracefully"
    - "LLM 500 failure loops hit max retry limit and halt instead of infinite looping"
  prohibitions: []
