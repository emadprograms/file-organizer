---
last_mapped_commit: HEAD
---
# Testing Practices

**Focus:** quality
**Date:** 2026-06-26

## Frameworks
- **pytest**: The primary testing framework, denoted by `pytest` in `requirements.txt` and the `tests/` folder.

## Test Structure
- `tests/` directory contains standard unit tests.
- `scripts/` contains several manual evaluation scripts (e.g., `evaluate_local.py`, `test_1273.py`, `check_models.py`) which serve as integration/smoke tests against local models or specific edge-case PDFs.

## Coverage
- Caching logic makes LLM testing easier by allowing test runs on pre-cached data without hitting real APIs.
