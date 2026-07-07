# Testing Patterns

**Date**: 2026-07-07

## 1. Testing Framework
- **Primary Framework**: The project utilizes `pytest` as its sole test runner and testing framework.
- **Structure**: Tests reside in the `tests/` directory at the project root, roughly mirroring the `src/` modules (e.g., `test_pipeline.py` tests `src/processing/pipeline.py`).
- **Configuration**: Common fixtures and setups are housed in `tests/conftest.py`.

## 2. Test Environments and Isolation
- **Filesystem Isolation**: File and directory manipulation logic is tested using pytest's built-in `tmp_path` fixture. This guarantees tests are isolated from the host filesystem and do not pollute the main repository.
- **End-to-End Dry Runs**: The system implements an E2E testing pattern (`test_e2e.py`) via a `--dry-run` flag that validates full orchestration and formatting outputs without altering physical files or making network requests.
- **Pre-baked Fixtures**: Test scenarios frequently utilize static JSON fixtures and minimalist PDF stand-ins (e.g., stored in `tests/fixtures/golden_1273/`) to guarantee deterministic tests and to skip earlier pipeline steps like LLM document extraction.

## 3. Mocking Strategy
- **Library Used**: Standard `unittest.mock` (`MagicMock`, `patch`) is utilized to stub out dependencies.
- **Network Bypass**: LLM API calls are explicitly mocked to prevent tests from requiring active internet connections, API keys, or consuming cloud quotas. 
- **Offline Fallback Mechanisms**: The CLI and core pipeline accept a `--skip-llm` flag (translating to a `skip_llm` property on the `LLMClient`), which explicitly bypasses API invocations and injects hardcoded mockup schemas. This allows robust E2E verification of pipeline routing logic without live LLMs.

## 4. Coverage and Assertions
- **Assertion Style**: Standard `assert` statements are used, enriched with detailed error messages (e.g., `assert result.returncode == 0, f"Exited with {result.returncode}. stdout:..."`).
- **CLI Output Validation**: Subprocess executions of the main CLI (`organize.py`) validate system behavior by asserting on process return codes and inspecting captured `stdout`/`stderr` strings for expected phrases.
- **Resiliency Verification**: Dedicated tests ensure the system handles invalid input gracefully. Examples include tests verifying that malformed JSON payloads lead to clean non-zero exits rather than unhandled stack traces, and tests verifying fallback routing behavior when out-of-bound references occur.
