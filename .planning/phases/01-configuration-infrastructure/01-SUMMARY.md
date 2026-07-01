# Plan 1 Summary: Configuration Infrastructure

## Work Completed
- Added `PyYAML` to `requirements.txt`.
- Defined `UserConfig`, `ConfigCategory`, `ConfigExtraction`, and `ConfigRouting` Pydantic models in `src/schemas.py`.
- Created `load_user_config` function and `InvalidConfigError` in `src/config.py` to securely parse and validate YAML/JSON configurations using `yaml.safe_load`.
- Updated `argparse` in `src/main.py` to accept an optional `-c` or `--config` flag to inject the user configuration. Handled failure by fast-failing via `sys.exit(1)`.
- Created `sample-config.yaml` in the project root containing the 13 foundational categories, extraction rules, and routing settings.
- Added `config.yaml` and `test-config.yaml` to `.gitignore` and provided a `test-config.yaml` for local test regression.

## Verification
- Running `python -c "from src.config import load_user_config; from pathlib import Path; load_user_config(Path('sample-config.yaml'))"` executes successfully.
- Running `python src/main.py non_existent.pdf --config invalid-config.yaml` properly fails fast.
