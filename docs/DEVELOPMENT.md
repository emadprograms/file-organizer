<!-- generated-by: gsd-doc-writer -->
# Development Guide

This document provides instructions for setting up the `file-organizer` project for local development, running tests, and contributing to the codebase.

## Local Setup

To develop `file-organizer` locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd file-organizer
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.\.venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy the example environment file and fill in the required values (e.g., API keys).
   ```bash
   cp .env.example .env
   ```

## Build Commands

As this is a Python project, there is no formal compilation or build step required before running the application. The primary command used during development is for executing the test suite.

| Command | Description |
|---------|-------------|
| `pytest` | Runs the full test suite in the `tests/` directory. |

## Code Style

No formal linting or formatting configuration (e.g., `flake8`, `black`, `mypy`) was detected in the project. 
- Please adhere to standard Python PEP 8 conventions.
- Maintain consistent formatting with the existing codebase.

## Branch Conventions

- **Default Branch**: `main`
- No specific branch naming convention is documented. It is recommended to use descriptive prefixes (e.g., `feat/`, `fix/`, `docs/`) followed by a brief summary.

## PR Process

To submit a pull request:
1. Create a new branch from `main`.
2. Commit your changes with descriptive messages.
3. Ensure all tests pass by running `pytest` locally.
4. Submit a Pull Request targeting the `main` branch.
5. Provide a clear summary of the changes made and the problem they solve.
