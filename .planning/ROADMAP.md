# Roadmap v1.3: Output Structure Refinement

## Phase 1: Output Path Logic Update

- Update `organize.py` to calculate `output_dir` as `args.target_dir / house_id`.
- Remove the conditional logic that checks if `args.target_dir.name == house_id`.
- Ensure all subsequent paths (cleaned JSON, checkpoints, manifest) use this new `output_dir`.
- Verify that `FileOrganizer.organize` receives the correct `output_base_dir` and correctly creates the `house_dir`.

## Phase 2: Validation & Testing

- Create a test case in `tests/test_cli.py` or a new test file to verify that the output folder is created exactly where expected, regardless of whether the target directory is the house folder or a parent folder.
- Run the pipeline in dry-run mode to verify directory creation for various input paths.
- Perform an E2E test with a real PDF to confirm the final structure.
