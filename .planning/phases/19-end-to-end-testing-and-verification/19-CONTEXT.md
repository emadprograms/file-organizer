# Phase 19: end-to-end-testing-and-verification - Context

**Gathered:** 2026-07-17T10:00:01+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

Fixing the testing structure, golden datasets, E2E routing verification, and dry run validation logic to ensure pipeline refactoring is robustly tested.

</domain>

<decisions>
## Implementation Decisions

### Test Suite Structure & Naming
- **D-01:** Keep test files flat in the `tests/` directory but strictly enforce `test_[module].py` naming convention. Every `uat_08_*.py`, `verify_*.py`, phase-numbered test, and opaque script must be **read, understood, and rewritten as a proper `pytest` module** with descriptive `def test_*()` functions — not just renamed. The new name must describe the behavior being tested, not the phase it was written in.

### Golden Dataset Input/Output Validation
- **D-02:** Retain the name `golden_1273`.
- **D-03:** Inside `golden_1273`, clearly separate the input folder (`1273` input file) and the output folder (the exact expected final folder structure and output files) so tests have a clear "golden" expected state to assert against.

### `.source_files` Directory Placement
- **D-04:** `.source_files` must be placed exactly inside the target house folder natively (e.g., `golden_1273/input/1273/.source_files/`) so the code finds the YAML configuration without custom test logic or data loss bugs.

### Dry Run and E2E Routing Testing
- **D-05:** Dry runs and E2E tests must use intermediate JSON files (e.g., `1273_cleaned.json`, `1273_grouped.json`, `1273_routed.json`) from the golden dataset.
- **D-06:** Mock the LLM responses at the function level during testing. The exact LLM responses should be saved (potentially by running the code once to capture them) and used to mock the responses exactly, bypassing actual LLM calls while verifying full routing logic.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Architecture
- `.planning/REQUIREMENTS.md` — To ensure legacy requirements like PIPE-02, PIPE-03, and YAML-01 are tested thoroughly.
- `src/tenant_config/yaml_loader.py` — The YAML loading logic that expects `.source_files` inside the target directory.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pytest` configuration in `tests/conftest.py` — May contain existing fixtures that need to be updated to match the new `golden_1273` structure.
- `src/pipeline/pipeline.py` and `src/main.py` — Core routing and dry-run execution logic to be mocked and tested.

### Established Patterns
- LLM mocking — Tests currently lack structured function-level LLM mocking for dry runs, which needs to be standardized.

### Integration Points
- Test execution connects with `pytest`. Mocking should integrate at the provider/LLM call boundary.

</code_context>

<specifics>
## Specific Ideas

- The user specifically requested: "mock the llm responses at function level to create the files in that manner. If you want, you can even run the code once. see the llm responses and save it and use it later to mock them exactly."

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 19-end-to-end-testing-and-verification*
*Context gathered: 2026-07-17T10:00:01+03:00*
