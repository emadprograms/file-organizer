# Phase 19 Research: End-to-End Testing and Verification

## Current State
The project has recently undergone significant refactoring for v2.0 (Phases 16-18.6):
- `src/` directory restructured into logical domains: `core`, `utils`, `tenant_config`, `grouping`, `timeline`, `routing`.
- Checkpoints system overhauled.
- YAML configuration logic introduced to replace anchor logic and extract primary tenant names.
- Pipeline now utilizes YAML tenant names for Pass 1 LLM extraction.
- PDF outputs are compressed and explicitly use `Tenant - Folder Name` metadata, with the `_finalized` suffix.
- LLM fallback handling (Gemini 3.5 Flash -> Gemini 3 Flash -> Gemini 2.5 Flash) added for resilience globally.

## Implications for E2E
Because of the above structural and logic changes, our tests will likely fail on:
1. `import` statements if they refer to old legacy module paths.
2. File outputs if the tests assert `_categorized.pdf` instead of `_finalized.pdf`.
3. Golden checkpoints and pipelines if assertions check for exact metadata properties that were changed.
4. YAML parsing tests must pass seamlessly without regressing tenant mapping logic.

## Strategy
To successfully execute Phase 19:
- Execute `pytest` and aggregate all errors.
- Methodically update test mocks, imports, and output assertions.
- Verify `--dry-run` behavior locally via CLI invocation.
- Do not make changes to business logic; only test setups and import paths should be altered unless a true regression is found.
