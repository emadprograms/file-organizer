---
wave: 1
depends_on: []
files_modified:
  - src/cleaning.py
  - src/cleaning/__init__.py
  - src/cleaning/models.py
  - src/cleaning/dates.py
  - src/cleaning/tenants.py
  - src/cleaning/phase.py
  - tests/test_cleaning.py
autonomous: true
requirements:
  - REF-01
---

# Phase 02: Refactor src/cleaning.py

**Requirements:** REF-01
**Phase Goal:** Refactor `src/cleaning.py` into separate focused modules based on responsibility without altering the existing functionality.

<threat_model>
- Not applicable for this pure refactoring phase (no new external inputs or logic changes).
</threat_model>

## must_haves
- D-01, D-02: All logic from `src/cleaning.py` is preserved and relocated to appropriate submodules inside `src/cleaning/`.
- D-03: Keep date parsing strictly encapsulated within the new cleaning package (e.g., `src/cleaning/dates.py`).
- The original `src/cleaning.py` file is removed.
- D-04: `src/cleaning/__init__.py` exposes `process_cleaning_phase` and `PageData` to maintain the facade pattern for consumers like `src/organize.py`.
- Tests in `tests/test_cleaning.py` are updated to import from the new submodules and all tests pass.
- No new features are added; behavior remains exactly the same.

## Artifacts this phase produces
- **New Directories:**
  - `src/cleaning/`
- **New Files:**
  - `src/cleaning/__init__.py`
  - `src/cleaning/models.py`
  - `src/cleaning/dates.py`
  - `src/cleaning/tenants.py`
  - `src/cleaning/phase.py`
- **Exported Symbols (Facade):**
  - `src.cleaning.process_cleaning_phase` (function)
  - `src.cleaning.PageData` (class)

## Tasks

<task>
  <action>
    Create the new package directory `src/cleaning/`. Then, extract models and date parsing logic from the existing `src/cleaning.py`.
    1. Create `src/cleaning/models.py` and move `PageData` and `TenantTimeline` classes into it.
    2. Create `src/cleaning/dates.py` and move `_ENGLISH_MONTH_MAP`, `_ARABIC_GREGORIAN_MONTH_MAP`, `_HIJRI_ARABIC_MONTH_MAP`, `_HIJRI_ENGLISH_MONTH_MAP`, `_WEEKDAY_PATTERN`, `_ORDINAL_SUFFIX`, `_hijri_to_gregorian`, `_is_hijri_year`, and `parse_flexible_date` into it.
  </action>
  <read_first>
    - src/cleaning.py
  </read_first>
  <acceptance_criteria>
    - `src/cleaning/models.py` contains `PageData` and `TenantTimeline` classes.
    - `src/cleaning/dates.py` contains all date maps, constants, and the `parse_flexible_date` function.
    - Both files import their required dependencies (`BaseModel`, `re`, etc.).
  </acceptance_criteria>
</task>

<task>
  <action>
    Extract tenant resolution logic and the main orchestrator phase from `src/cleaning.py`.
    1. Create `src/cleaning/tenants.py` and move `normalize_arabic_text`, `cluster_names_fuzzily`, `canonicalize_with_llm`, `build_tenant_timelines` into it. Ensure it imports `PageData` and `TenantTimeline` from `src.cleaning.models`.
    2. Create `src/cleaning/phase.py` and move `load_and_parse_json`, `infer_missing_dates`, `assign_pages_to_tenants`, and `process_cleaning_phase` into it. Ensure it imports from `src.cleaning.models`, `src.cleaning.dates`, and `src.cleaning.tenants` as needed.
  </action>
  <read_first>
    - src/cleaning.py
  </read_first>
  <acceptance_criteria>
    - `src/cleaning/tenants.py` contains the tenant resolution functions.
    - `src/cleaning/phase.py` contains the main orchestration functions.
    - Functions in both files correctly import their dependencies from sibling modules inside `src/cleaning`.
  </acceptance_criteria>
</task>

<task>
  <action>
    Establish the facade pattern in `src/cleaning/__init__.py` and remove the legacy file.
    1. Create `src/cleaning/__init__.py` and write `from .models import PageData` and `from .phase import process_cleaning_phase` inside it.
    2. Delete the old `src/cleaning.py` file.
  </action>
  <read_first>
    - src/organize.py
    - src/cleaning.py
  </read_first>
  <acceptance_criteria>
    - `src/cleaning/__init__.py` exists and exports `PageData` and `process_cleaning_phase`.
    - The file `src/cleaning.py` no longer exists.
    - Running `python src/organize.py --help` works without `ImportError`.
  </acceptance_criteria>
</task>

<task>
  <action>
    Update `tests/test_cleaning.py` to import internal functions from their new modular locations instead of directly from `src.cleaning`.
    1. Update the import block to import `PageData`, `TenantTimeline` from `src.cleaning.models`.
    2. Update to import `parse_flexible_date` from `src.cleaning.dates`.
    3. Update to import `normalize_arabic_text`, `cluster_names_fuzzily`, `canonicalize_with_llm`, `build_tenant_timelines` from `src.cleaning.tenants`.
    4. Update to import `load_and_parse_json`, `infer_missing_dates`, `assign_pages_to_tenants`, `process_cleaning_phase` from `src.cleaning.phase`.
    5. Find the monkeypatching call `monkeypatch.setattr("src.cleaning.assign_pages_to_tenants", lambda p, t: None)` and update it to monkeypatch `"src.cleaning.phase.assign_pages_to_tenants"`.
  </action>
  <read_first>
    - tests/test_cleaning.py
  </read_first>
  <acceptance_criteria>
    - `tests/test_cleaning.py` imports internal module functions correctly.
    - The `monkeypatch` path is correctly set to `"src.cleaning.phase.assign_pages_to_tenants"`.
    - Running `python -m pytest tests/test_cleaning.py` passes with no errors.
  </acceptance_criteria>
</task>

## Verification
- Run `python -m pytest tests/` and verify all tests pass.
- Verify `src/cleaning/` exists and contains `models.py`, `dates.py`, `tenants.py`, `phase.py`, and `__init__.py`.
- Verify `src/cleaning.py` is removed.
- Run `python src/organize.py --help` to ensure `src/organize.py` runs successfully.
