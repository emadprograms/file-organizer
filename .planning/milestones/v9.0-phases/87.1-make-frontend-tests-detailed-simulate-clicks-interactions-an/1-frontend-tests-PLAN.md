---
phase: 87.1
plan: 1
type: test
wave: 1
depends_on: []
files_modified:
  - tests/frontend/test_dashboard.py
  - src/frontend/app.py
  - src/backend/api.py
autonomous: true
requirements: []
---

<objective>
Update the frontend tests to deeply verify category numbering and click interactions, preventing shallow tests. Also apply the required fixes so the tests pass.
</objective>

<tasks>
1. `type: test`, `files: tests/frontend/test_dashboard.py`, `action: update`, `verify: run pytest tests/frontend/test_dashboard.py`, `acceptance_criteria: tests assert category numbering and pdf clicking`
2. `type: feature`, `files: src/backend/api.py, src/frontend/app.py`, `action: update`, `verify: run pytest tests/frontend/test_dashboard.py`, `acceptance_criteria: api returns documents, frontend categories are clickable, category names have numbers`
</tasks>

<verification>
Run all frontend tests: `pytest tests/frontend/test_dashboard.py` and ensure they pass.
</verification>

<success_criteria>
- Tests check that clicking on a category opens PDFs
- Tests check that categories display with correct numbers
- The actual implementation is fixed to support this
</success_criteria>
