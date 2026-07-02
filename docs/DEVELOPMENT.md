<!-- generated-by: gsd-doc-writer -->
# Development

## Local Setup
To set up the project for development:
1. **Clone and Install**: Follow the steps in [GETTING-STARTED.md](docs/GETTING-STARTED.md).
2. **Environment Configuration**: Copy `.env.example` (if available) to `.env` and populate your API keys.
3. **Logging**: The system automatically creates a `logs/` directory. You can monitor the application's progress by tailing the latest `_app.log` file.

## Build Commands
The project is a pure Python application and does not require a compilation step.

| Command | Description |
|:---|:---|
| `python src/main.py <pdf_path> -c <config.yaml>` | Run the core categorization pipeline with a specified config |
| `pytest` | Run the full test suite |
| `pytest tests/test_pipeline.py` | Run only pipeline-related tests |

## Code Style
The project adheres to standard Python PEP 8 guidelines. While no automated linter is enforced in the repository, it is recommended to use:
- **Black**: For consistent code formatting.
- **Flake8** or **Ruff**: For linting.

## Branch Conventions
No formal branch naming convention is documented. It is recommended to use feature-based naming:
- `feat/description` for new features.
- `fix/description` for bug fixes.

## PR Process
1. **Fork and Branch**: Create a feature branch from `main`.
2. **Test**: Ensure all tests in the `tests/` directory pass before submitting.
3. **Submit**: Create a Pull Request with a clear description of the changes and the problem they solve.
4. **Review**: Changes must be reviewed by a maintainer before merging.
