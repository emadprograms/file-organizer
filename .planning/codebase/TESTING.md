# Testing Patterns

**Analysis Date:** 2026-07-07

## Test Framework

**Runner:**
- pytest
- Config: `tests/conftest.py`

**Assertion Library:**
- Standard `assert` statements.

**Run Commands:**
```bash
pytest              # Run all tests
pytest -v           # Verbose output
pytest tests/test_llm.py # Run specific test file
```

## Test File Organization

**Location:**
- Separate `tests/` directory at the root.

**Naming:**
- `test_*.py` (e.g., `test_cleaning.py`, `test_pipeline.py`).

**Structure:**
```
tests/
├── fixtures/           # Static data for tests
└── test_[module].py    # Tests corresponding to src/[module].py
```

## Test Structure

**Suite Organization:**
```python
def test_llm_client_failover():
    # Setup mock providers
    # Execute call
    # Assert failover happened
```

**Patterns:**
- **Mocking:** Extensive use of mocks for LLM API calls to avoid costs and dependencies during testing (`tests/test_llm.py`).
- **Integration Testing:** `test_e2e.py` provides an end-to-end flow check of the pipeline.
- **Fixture-based setup:** `conftest.py` defines shared fixtures for test environment initialization.

## Mocking

**Framework:** `unittest.mock`

**Patterns:**
```python
from unittest.mock import MagicMock
mock_provider = MagicMock()
mock_provider.generate.return_value = expected_response
```

**What to Mock:**
- All external LLM API calls.
- File system writes (where possible) to avoid cluttering the workspace.

**What NOT to Mock:**
- Core Pydantic schema validation logic.
- Local utility functions in `src/core/utils.py`.

## Fixtures and Factories

**Test Data:**
- JSON files and sample PDFs are stored in `tests/fixtures/`.

**Location:**
- `tests/fixtures/`

## Coverage

**Requirements:** Not explicitly enforced via config, but the test suite is comprehensive, covering almost every module in `src/`.

**View Coverage:**
```bash
pytest --cov=src
```

## Test Types

**Unit Tests:**
- Focus on individual functions (e.g., `test_fs_utils.py`, `test_schemas.py`).

**Integration Tests:**
- Focus on the interaction between modules (e.g., `test_pipeline.py`, `test_grouping.py`).

**E2E Tests:**
- `test_e2e.py` verifies the full path from input PDF to organized output.

## Common Patterns

**Async Testing:**
- The codebase uses `ThreadPoolExecutor` rather than `asyncio`, so tests are primarily synchronous.

**Error Testing:**
- Tests specifically verify that the LLM client handles 429 and 500 errors correctly (`tests/test_fallback_chain.py`).

---

*Testing analysis: 2026-07-07*
