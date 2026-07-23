<!-- generated-by: gsd-doc-writer -->
# Testing

## Test Framework and Setup

The project uses **pytest** as its primary testing framework. 

Before running tests, ensure you have set up your virtual environment and installed the testing dependencies (which are included in the main requirements file):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

To run the full test suite:

```bash
pytest
```

To run tests in a specific file:

```bash
pytest tests/test_core_config_parsing.py
```
*(On Windows using the local venv: `.\venv\Scripts\pytest`)*

To run a specific test case by its name:

```bash
pytest -k "test_record_successful_call"
```

To run tests with output enabled (useful for debugging):

```bash
pytest -s
```

## Writing New Tests

- **File Naming Convention:** All test files must be prefixed with `test_` (e.g., `test_routing_router.py`) and be placed inside the `tests/` directory to be discovered by pytest automatically.
- **Shared Fixtures:** Common test helpers and fixtures are located in `tests/conftest.py`. You can use fixtures like `mock_page_data_dict` and `mock_tenant_timeline_dict` to quickly inject standard mock data into your tests without rewriting boilerplate.
- **Static Test Data:** Static files, JSON states (e.g., `continuity_test_state.json`), and reference directories are stored in `tests/fixtures/`.
- **Mocking:** Rely on `pytest`'s built-in `monkeypatch` fixture to safely override configuration values or system calls, and `tmp_path` to generate temporary files and directories.

## Coverage Requirements

No coverage threshold configured.

## CI Integration

No CI/CD pipeline detected. Tests are currently run manually.
