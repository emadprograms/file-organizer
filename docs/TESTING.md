<!-- generated-by: gsd-doc-writer -->
# Testing

## Test Framework and Setup
The project uses **pytest** as its primary testing framework.

**Dependencies**: `pytest` is listed in `requirements.txt`.
**Setup**: Ensure your virtual environment is active and dependencies are installed.

## Running Tests
You can run tests from the project root:

**Run all tests:**
```bash
pytest
```

**Run specific test modules:**
```bash
pytest tests/test_pipeline.py
```

**Run with verbose output:**
```bash
pytest -v
```

## Writing New Tests
- **Naming Convention**: Test files must be prefixed with `test_` (e.g., `tests/test_organizer.py`).
- **Test Structure**: Use `conftest.py` for shared fixtures (e.g., mock LLM responses, sample PDF paths).
- **Patterns**: 
    - Use `pytest.mark.parametrize` for testing multiple PDF samples.
    - Use mocks (via `unittest.mock` or `pytest-mock`) to avoid making real API calls to LLMs during unit tests.

## Coverage Requirements
No strict coverage thresholds are currently configured in the repository. It is recommended to maintain high coverage for the `src/pipeline.py` and `src/organizer.py` modules as they contain the core business logic.

## CI Integration
CI is not currently configured. Tests are intended to be run locally by developers before submitting pull requests.
