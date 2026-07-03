---
wave: 3
depends_on: ["02-PLAN.md"]
files_modified:
  - "src/organize.py"
  - "tests/test_cli.py"
autonomous: true
---

# Phase 01: Foundation & Infrastructure (Wave 3 - CLI Entry Point)

## Goal
Build the CLI entry point (`organize.py`) with argument parsing and strict validation of the input directory and environment.

## Requirements Covered
- INIT-01: CLI accepts a single directory path argument
- INIT-02: Fail fast if `[ID]_categorized.pdf` is missing or misnamed
- INIT-03: Fail fast if `[ID]_report.json` is missing or misnamed
- INIT-04: Fail fast if `GEMINI_API_KEY` is missing
- INIT-05: Derive house number from PDF filename
- INIT-06: Create output directory at `./[source_dir]/output/`
- INIT-07: CLI `--model` flag to switch between default and `gemma-4-31b-it`

## Artifacts this phase produces
- `src/organize.py` (file)
- `src/organize.py:main` (function)
- `src/organize.py:validate_environment` (function)
- `src/organize.py:validate_target_directory` (function)
- `tests/test_cli.py` (file)

<threat_model>
ASVS Level: 1
Block On: high
Threats:
- T-01: Execution with missing or malformed data leading to unpredictable state.
  Mitigation: `validate_target_directory` strict enforcement before any logic runs.
</threat_model>

## Tasks

<task id="03-01" read_first="src/organize.py">
  <action>Create `src/organize.py` with `argparse`. Accept a positional argument for the target directory path and an optional `--model` flag (defaulting to `gemma-4-26b-a4b-it`). Implement `validate_environment` using `dotenv` to load and enforce the presence of `GEMINI_API_KEY`.</action>
  <acceptance_criteria>
    - `pytest tests/test_cli.py` passes
    - `python src/organize.py --help` outputs correctly.
    - Fails fast and exits if `GEMINI_API_KEY` is missing from the environment.
  </acceptance_criteria>
</task>

<task id="03-02" read_first="src/organize.py">
  <action>Implement `validate_target_directory(target_dir: Path)` in `src/organize.py`. It must assert the existence of exactly one `*_categorized.pdf` and one `*_report.json` with matching ID prefixes, gracefully handling missing files or multiple glob matches by printing a user-friendly error and exiting safely (no raw `IndexError`). Extract this `[ID]` as the house number (INIT-05). Create the `./[source_dir]/output/` subdirectory (INIT-06). Fail fast if any condition is unmet.</action>
  <acceptance_criteria>
    - `pytest tests/test_cli.py` passes
    - CLI properly extracts the house number from valid directories.
    - CLI fails gracefully with appropriate user-friendly error messages for missing, mismatched, or duplicate input files without throwing raw exceptions.
  </acceptance_criteria>
</task>

<task id="03-03" read_first="src/organize.py">
  <action>In `src/organize.py:main`, instantiate the `setup_logging` from `src/logger.py` and print starting messages line-by-line exactly as they appear in the log file (D-03). Instantiate the `LLMClient` with the model parsed from the CLI flag. Exit cleanly with 0 upon successful validation (as later phases will attach processing logic here).</action>
  <acceptance_criteria>
    - `pytest tests/test_cli.py` passes
    - `python src/organize.py ./pdfs/1273` validates file pair existence and exits cleanly with 0 if successful, or non-zero with error if missing.
  </acceptance_criteria>
</task>

## Verification
<verify>
  `pytest tests/test_cli.py` passes successfully, asserting failure codes and stderr outputs on missing keys or files.
</verify>

## Must Haves
must_haves:
  truths:
    - `python organize.py ./pdfs/1273` validates file pair existence and exits cleanly with error if missing.
    - `python organize.py ./pdfs/1273 --model gemma-4-31b-it` accepts model flag.
